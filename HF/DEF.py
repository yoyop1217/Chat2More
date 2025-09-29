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

# 2-2. Rewrite
async def rewrite_once(model_key, text, system_prompt, temp):
    try:
        if not text or not text.strip():
            return "⚠️ 請輸入文字"
        
        if model_key not in STIMA_MODELS:
            return f"⚠️ 找不到模型 {model_key}"
        
        _, full_id = STIMA_MODELS[model_key]
        client = get_client()
        
        # Build Messages
        messages = [
            {"role": "system", "content": system_prompt or "You are a helpful assistant. Respond in valid Markdown format."},
            {"role": "user", "content": text}
        ]
        
        print(f"[{datetime.now()}] 呼叫模型: {full_id}")
        print(f"[{datetime.now()}] 訊息內容: {messages}")
        
        # Called API
        try:
            # 檢測是否為 Gemini 模型，強制文字格式
            response_format = {"type": "text"} if "gemini" in full_id.lower() else None
            
            resp = await client.chat.completions.create(
                model=full_id,
                messages=messages,
                temperature=temp,
                max_tokens=9000,
                timeout=90
            )
            
            print(f"[{datetime.now()}] API 回應類型: {type(resp)}")
            print(f"[{datetime.now()}] API 回應內容: {resp}")
            
            # Check the return
            if isinstance(resp, str):
                try:
                    resp_data = json.loads(resp)
                    if 'error' in resp_data:
                        return f"⚠️ API 錯誤：{resp_data['error']}"
                    return f"⚠️ 未預期的字串回應：{resp}"
                except json.JSONDecodeError:
                    # 若非 JSON，假設為純文字內容，直接返回（Gemini 常見)
                    # 清理可能的 HTML 或多餘標記**
                    cleaned_resp = re.sub(r'<[^>]+>', '', resp) if 're' in globals() else resp  # 簡單 HTML 移除
                    return f"**Gemini 回應**：\n{cleaned_resp.strip()}" if cleaned_resp.strip() else f"**⚠️ 無法解析的回應**：{resp}"
                    return f"⚠️ 無法解析的回應：{resp}"
            
            if not hasattr(resp, 'choices'):
                return f"⚠️ API 回應格式不正確 (缺少 choices)\n回應類型: {type(resp)}\n回應內容: {str(resp)}"
            
            if not resp.choices or len(resp.choices) == 0:
                return "⚠️ API 回應中沒有選項"
            
            choice = resp.choices[0]
            if not hasattr(choice, 'message'):
                return f"⚠️ API 回應格式不正確 (缺少 message)\n選項內容: {str(choice)}"
            
            message = choice.message
            if not hasattr(message, 'content'):
                return f"⚠️ API 回應格式不正確 (缺少 content)\n訊息內容: {str(message)}"
            
            # Get Content
            content = message.content
            if content is None:
                return "⚠️ 模型回應為空"
            
            return content.strip()
            
        except openai.APIConnectionError as e:
            return f"⚠️ 連線錯誤：無法連接到 API 服務\n詳細：{str(e)}"
        except openai.RateLimitError as e:
            return f"⚠️ 速率限制：API 請求過於頻繁\n詳細：{str(e)}"
        except openai.APIStatusError as e:
            return f"⚠️ API 錯誤 (狀態碼 {e.status_code})：{e.message}\n詳細：{str(e)}"
        except openai.APITimeoutError as e:
            return f"⚠️ 超時錯誤：API 回應時間過長\n詳細：{str(e)}"
        except httpx.ConnectError as e:
            return f"⚠️ 網路連線錯誤：無法連接到伺服器\n詳細：{str(e)}"
        except httpx.TimeoutException as e:
            return f"⚠️ 網路超時：請求超時\n詳細：{str(e)}"
        except Exception as e:
            error_detail = traceback.format_exc()
            return f"⚠️ API 呼叫錯誤：{type(e).__name__}\n錯誤：{str(e)}\n\n詳細追蹤:\n{error_detail}"
            
    except Exception as e:
        error_detail = traceback.format_exc()
        return f"⚠️ 未預期的錯誤：{type(e).__name__}\n{str(e)}\n\n詳細資訊:\n{error_detail}"

# 2-3. Batch Rewrite
def rewrite_batch(text, model1, model2, model3, sys_prompt, temp):
    if not text or not text.strip():
        return ("請輸入要改寫的文字", "請輸入要改寫的文字", "請輸入要改寫的文字")
    
    async def _run():
        tasks = [
            rewrite_once(model1, text, sys_prompt, temp),
            rewrite_once(model2, text, sys_prompt, temp),
            rewrite_once(model3, text, sys_prompt, temp)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        model_names = [model1, model2, model3]
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"模型 {model_names[i]} 執行錯誤：\n{type(result).__name__}\n{str(result)}"
                processed_results.append(error_msg)
            else:
                processed_results.append(result)
        
        return processed_results
    
    try:
        return asyncio.run(_run())
    except Exception as e:
        error_msg = f"批次執行錯誤：{type(e).__name__}\n{str(e)}"
        return (error_msg, error_msg, error_msg)

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


