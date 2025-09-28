import os
from DEF import STIMA_KEY
from models_list import STIMA_MODELS
from DEMO import demo

model_list = list(STIMA_MODELS.keys())

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
