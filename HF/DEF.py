import os
import asyncio
import openai
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI
import traceback
import json
from datetime import datetime
from models_list import STIMA_MODELS

# 1️⃣ ENV
load_dotenv()
TIMEOUT = 60
## 1-1. STIMA_env
STIMA_KEY = os.getenv("STIMA_API_KEY")
STIMA_URL = "https://api.stima.tech/v1"

# 2️⃣ SET
## 2-1. Client
def get_client():
    if not STIMA_KEY:
        raise ValueError("STIMA_API_KEY 未設置")
    return AsyncOpenAI(
        api_key=STIMA_KEY,
        base_url=STIMA_URL,
        timeout=TIMEOUT
    )

# 2-2. Rewrite（實現分段生成與分段顯示）
async def rewrite_once(model_key, text, system_prompt, temp):
    try:
        if not text or not text.strip():
            return "⚠️ 請輸入文字"
        
        if model_key not in STIMA_MODELS:
            return f"⚠️ 找不到模型 {model_key}"
        
        _, full_id = STIMA_MODELS[model_key]
        client = get_client()
        
        # Build Messages（優化為分段生成提示）
        messages = [
            {"role": "system", "content": system_prompt or "You are a helpful assistant. Respond concisely in valid Markdown format. For long responses, provide a summary first, then continue with details on request."},
            {"role": "user", "content": text}
        ]
        
        print(f"[{datetime.now()}] 呼叫模型: {full_id}")
        print(f"[{datetime.now()]] 訊息內容: {messages}")
        
        # Called API（分段處理與顯示）
        try:
            # 檢測是否為深研模型，調整參數
            is_deep_research = "sonar-pro" in full_id.lower() or "deep-research" in full_id.lower()
            response_format = {"type": "text"} if "gemini" in full_id.lower() else None
            max_tokens_per_call = 500  # 每次分段生成 500 token
            timeout = 90 if not is_deep_research else 120  # 深研模型增加超時
            
            content = ""
            current_messages = messages.copy()
            first_segment = True
            
            while True:
                resp = await client.chat.completions.create(
                    model=full_id,
                    messages=[{"role": "system", "content": "Continue the previous response or provide a summary if starting."}, *current_messages],
                    temperature=temp,
                    max_tokens=max_tokens_per_call,
                    timeout=timeout,
                    response_format=response_format
                )
                
                print(f"[{datetime.now()}] API 回應類型: {type(resp)}")
                print(f"[{datetime.now()}] API 回應內容: {resp}")
                
                # 處理回應並逐步返回
                new_content = ""
                if isinstance(resp, str):
                    try:
                        resp_data = json.loads(resp)
                        if 'error' in resp_data:
                            return f"⚠️ API 錯誤：{resp_data['error']}"
                        new_content = resp_data.get('choices', [{}])[0].get('message', {}).get('content', resp) or ""
                    except json.JSONDecodeError:
                        cleaned_resp = re.sub(r'<[^>]+>', '', resp) if 're' in globals() else resp
                        new_content = cleaned_resp.strip() or ""
                elif hasattr(resp, 'choices') and resp.choices:
                    choice = resp.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        new_content = choice.message.content.strip()
                        # 更新 messages 為下次續寫
                        current_messages = [
                            {"role": "system", "content": "Continue the previous response."},
                            {"role": "user", "content": new_content}
                        ]
                    else:
                        break
                else:
                    break
                
                if new_content:
                    content += new_content
                    # 逐步返回分段內容
                    if first_segment:
                        yield f"**摘要或開始**：\n{new_content}"
                        first_segment = False
                    else:
                        yield f"**續寫**：\n{new_content}"
                
                # 檢查是否為完整回應
                if len(new_content.split()) < max_tokens_per_call or "summary" in content.lower() or "end" in content.lower():
                    break
            
            # 最終返回完整內容（可選，確保最後顯示）
            if content.strip():
                yield f"**完整回應**：\n{content.strip()}"
            else:
                yield "⚠️ 回應生成中斷"
            
        except openai.APIConnectionError as e:
            yield f"⚠️ 連線錯誤：無法連接到 API 服務\n詳細：{str(e)}"
        except openai.RateLimitError as e:
            yield f"⚠️ 速率限制：API 請求過於頻繁\n詳細：{str(e)}"
        except openai.APIStatusError as e:
            if e.status_code == 504:
                yield f"⚠️ 閘道超時 (504)：上游伺服器延遲，請稍後重試或分段查詢\n- 詳細：{str(e)}"
            else:
                yield f"⚠️ API 錯誤 (狀態碼 {e.status_code})：{e.message}\n詳細：{str(e)}"
        except openai.APITimeoutError as e:
            yield f"⚠️ 超時錯誤：API 回應時間過長，請縮短 prompt 或分段查詢\n詳細：{str(e)}"
        except httpx.ConnectError as e:
            yield f"⚠️ 網路連線錯誤：無法連接到伺服器\n詳細：{str(e)}"
        except httpx.TimeoutException as e:
            yield f"⚠️ 網路超時：請求超時\n詳細：{str(e)}"
        except Exception as e:
            error_detail = traceback.format_exc()
            yield f"⚠️ API 呼叫錯誤：{type(e).__name__}\n錯誤：{str(e)}\n\n詳細追蹤:\n{error_detail}"
            
    except Exception as e:
        error_detail = traceback.format_exc()
        yield f"⚠️ 未預期的錯誤：{type(e).__name__}\n{str(e)}\n\n詳細資訊:\n{error_detail}"

# 2-3. Batch Rewrite（支持分段顯示）
async def rewrite_batch(text, model1, model2, model3, sys_prompt, temp):
    if not text or not text.strip():
        yield ("請輸入要改寫的文字", "請輸入要改寫的文字", "請輸入要改寫的文字")
        return
    
    async def process_model(model_key, index):
        try:
            async for segment in rewrite_once(model_key, text, sys_prompt, temp):
                yield index, segment
        except Exception as e:
            error_msg = f"模型 {model_key} 執行錯誤：\n{type(e).__name__}\n{str(e)}"
            yield index, error_msg
    
    # 並行處理三個模型
    tasks = [
        process_model(model1, 0),
        process_model(model2, 1),
        process_model(model3, 2)
    ]
    
    # 追蹤每個模型的最新段落
    outputs = ["", "", ""]
    async for updates in asyncio.gather(*tasks):
        for index, segment in updates:
            if segment:
                outputs[index] = segment
                yield (gr.Markdown.update(value=outputs[0]),
                       gr.Markdown.update(value=outputs[1]),
                       gr.Markdown.update(value=outputs[2]))
    
    # 最終確保所有輸出完成
    yield (gr.Markdown.update(value=outputs[0]),
           gr.Markdown.update(value=outputs[1]),
           gr.Markdown.update(value=outputs[2]))


# 2-4. Test Single Model
def test_single_model(text, model_key, sys_prompt, temp):
    if not text or not text.strip():
        return "請輸入測試文字"
    
    async def _test():
        return await rewrite_once(model_key, text, sys_prompt, temp)
    
    try:
        return asyncio.run(_test())
    except Exception as e:
        error_detail = traceback.format_exc()
        return f"測試執行錯誤：{type(e).__name__}\n{str(e)}\n\n詳細資訊:\n{error_detail}"

# 3️⃣ Test API Connection
def test_api_connection():
    async def _test():
        try:
            client = get_client()
            resp = await client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                timeout=10
            )
            return f"API 連線正常\n回應類型: {type(resp)}"
        except Exception as e:
            return f"API 連線測試失敗: {type(e).__name__}\n{str(e)}"
    
    try:
        return asyncio.run(_test())
    except Exception as e:
        return f"連線測試執行錯誤: {type(e).__name__}\n{str(e)}"




