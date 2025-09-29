import gradio as gr
from models_list import STIMA_MODELS
from DEF import test_api_connection, test_single_model, rewrite_batch

model_list = list(STIMA_MODELS.keys())

# 更新 CSS，改為白色底框與淺藍邊框
custom_css = """
.markdown-output {
    border: 2px solid #E6F7FF; /* 淺藍色邊框 */
    border-radius: 5px; /* 圓角效果 */
    padding: 10px; /* 內邊距 */
    background-color: #ffffff; /* 純白色背景 */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* 輕微陰影 */
    max-height: 600px; /* 最大高度，超過時滾動 */
    overflow-y: auto; /* 垂直滾動條 */
    resize: vertical; /* 允許用戶手動調整高度 */
}

/* 確保外層容器不生成額外滾動條 */
.gr-row {
    overflow: hidden; /* 阻止外層滾動 */
    height: auto; /* 自動適應內部高度 */
}
"""

with gr.Blocks(theme=gr.themes.Soft(), title="Chat-2-More", css=custom_css) as demo:
    gr.Markdown("# 📝 比較多種模型的輸出結果（with StimaAPI）")
    gr.Markdown("---")
    gr.Markdown("""
    ⚠️ **注意事項：**
    - 使用前先使用 **🔧 API 測試工具** 測試 API_Key 可用性，確認尚有額度，若有錯誤，請至[ITHome文章頁面](https://ithelp.ithome.com.tw/articles/10391018)回報
    - 部分模型可能需要較長回應時間，請耐心等待
    - 鑒於 Stima API 部分模型不太穩定，若使用時有報錯，可至 **🔧 單一模型測試** 檢查是否為單一模型問題
    """)
    
    # API 連線測試區域
    with gr.Accordion("🔧 API 測試工具", open=False):
        test_btn = gr.Button("測試 API 連線")
        test_result = gr.Markdown(
            label="測試結果", 
            elem_classes=["markdown-output"],
            max_height=300
        )
        test_btn.click(test_api_connection, outputs=[test_result])
    
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
    
    with gr.Row(elem_classes=["gr-row"]):
        default_idx1 = min(0, len(model_list) - 1)
        default_idx2 = min(21, len(model_list) - 1)
        default_idx3 = min(82, len(model_list) - 1)
        
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

    with gr.Row(elem_classes=["gr-row"]):
        out1 = gr.Markdown(
            label="模型 1 輸出", 
            elem_classes=["markdown-output"],
            max_height=600
        )
        out2 = gr.Markdown(
            label="模型 2 輸出", 
            elem_classes=["markdown-output"],
            max_height=600
        )
        out3 = gr.Markdown(
            label="模型 3 輸出", 
            elem_classes=["markdown-output"],
            max_height=600
        )

    # 單一模型測試
    with gr.Accordion("🔧 單一模型測試", open=False):
        with gr.Row(elem_classes=["gr-row"]):
            test_text = gr.Textbox(label="測試文字", value="Hello, how are you?")
            test_model = gr.Dropdown(model_list, value=model_list[0] if model_list else "", label="測試模型")
        
        single_test_btn = gr.Button("測試單一模型")
        single_result = gr.Markdown(
            label="單一模型測試結果", 
            elem_classes=["markdown-output"],
            max_height=400
        )
        single_test_btn.click(
            test_single_model,
            inputs=[test_text, test_model, sys_prompt, temp],
            outputs=[single_result]
        )

    # 綁定主要查詢按鈕
    btn.click(
        fn=rewrite_batch,
        inputs=[src, dd1, dd2, dd3, sys_prompt, temp],
        outputs=[out1, out2, out3]
    )

if __name__ == "__main__":
    demo.launch()
