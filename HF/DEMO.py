import gradio as gr
from models_list import STIMA_MODELS
import DEF

model_list = list(STIMA_MODELS.keys())

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
