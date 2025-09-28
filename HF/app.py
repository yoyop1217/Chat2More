import os
import asyncio
import openai
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI
import traceback
import json
import gradio as gr
from models_list import STIMA_MODELS

model_list = list(STIMA_MODELS.keys())

# 1️⃣ ENV
load_dotenv()
TIMEOUT = 60
## 1-1. STIMA_env
STIMA_KEY = os.getenv("STIMA_API_KEY")
STIMA_URL = "https://api.stima.tech/v1"


# 2️⃣ SET
## 2-1. Client
def get_client():
    return AsyncOpenAI(
        api_key=STIMA_KEY,
        base_url=STIMA_URL,
        timeout=TIMEOUT
    )

# 2-2. Rewirte
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
            {"role": "system", "content": system_prompt or "You are a helpful assistant."},
            {"role": "user", "content": text}
        ]
        
        print(f"呼叫模型: {full_id}")
        print(f"訊息內容: {messages}")
        
        # Called API
        try:
            resp = await client.chat.completions.create(
                model=full_id,
                messages=messages,
                temperature=temp,
                max_tokens=2000,
                timeout=60
            )
            
            print(f"API 回應類型: {type(resp)}")
            print(f"API 回應內容: {resp}")
            
            # Check the return
            if isinstance(resp, str):
                try:
                    resp_data = json.loads(resp)
                    if 'error' in resp_data:
                        return f"⚠️ API 錯誤：{resp_data['error']}"
                    return f"⚠️ 未預期的字串回應：{resp}"
                except json.JSONDecodeError:
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
    # check empty
    if not text or not text.strip():
        return ("請輸入要改寫的文字", "請輸入要改寫的文字", "請輸入要改寫的文字")
    
    async def _run():
        # set up tasks, allow concurrent execution
        tasks = [
            rewrite_once(model1, text, sys_prompt, temp),
            rewrite_once(model2, text, sys_prompt, temp),
            rewrite_once(model3, text, sys_prompt, temp)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # process results
        processed_results = []
        model_names = [model1, model2, model3]
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # If an exception occurred, format it nicely
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


# 3️⃣ Test API Connection
def test_api_connection():
    async def _test():
        try:
            client = get_client()
            # Use a common model for testing
            resp = await client.chat.completions.create(
                model="gpt-4.1-nano", # A small, fast, and cost-effective GPT-4 variant
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

with gr.Blocks(theme=gr.themes.Soft(), title="Chat-2-More") as demo:
    gr.Markdown("# 📝 比較多種模型的輸出結果（with StimaAPI）")
    
    # 主要功能區域
    src = gr.Textbox(
        label="輸入字句", 
        lines=8, 
        placeholder="如：請幫我解釋什麼是量子電腦？",
        value=""
    )
    
    sys_prompt = gr.Textbox(
        label="自訂系統提示 (可空白)", 
        placeholder="如：用大學生的口吻回答",
        value=""
    )

    temp = gr.Slider(
        0.0, 1.0, 
        value=0.7,
        step=0.05, 
        label="Temperature (0=保守, 1=創意)"
    )
    
    with gr.Row():
        # 
        default_idx1 = min(4, len(model_list)-1) if len(model_list) > 4 else 0
        default_idx2 = min(41, len(model_list)-1) if len(model_list) > 41 else min(1, len(model_list)-1)
        default_idx3 = min(151, len(model_list)-1) if len(model_list) > 151 else min(2, len(model_list)-1)
        
        dd1 = gr.Dropdown(
            model_list, 
            value=model_list[default_idx1] if model_list else None, 
            label="模型 1"
        )
        dd2 = gr.Dropdown(
            model_list, 
            value=model_list[default_idx2] if model_list else None, 
            label="模型 2"
        )
        dd3 = gr.Dropdown(
            model_list, 
            value=model_list[default_idx3] if model_list else None, 
            label="模型 3"
        )

    btn = gr.Button("🌟 開始查詢", variant="primary")

    with gr.Row():
        out1 = gr.Textbox(label="模型 1 輸出", lines=20)
        out2 = gr.Textbox(label="模型 2 輸出", lines=20)
        out3 = gr.Textbox(label="模型 3 輸出", lines=20)  

if __name__ == "__main__":
    # 檢查環境變數
    if not STIMA_KEY:
        print("⚠️ STIMA_API_KEY 環境變數未設定！")
    else:
        print("✅ STIMA_API_KEY 已設定")
    
    # 檢查模型清單
    if not model_list:
        print("⚠️ models_list.py 中沒有找到模型！")
    else:
        print(f"✅ 找到 {len(model_list)} 個模型")
    
    demo.launch(server_name="0.0.0.0", server_port=7860)
