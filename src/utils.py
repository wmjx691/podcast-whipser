import os
import sys

def detect_environment():
    """偵測目前是否在 Google Colab 環境中執行"""
    return "COLAB_RELEASE_TAG" in os.environ or 'google.colab' in sys.modules

def get_project_root():
    """獲取專案根目錄 (單一真相來源)"""
    if detect_environment():
        # Colab 路徑
        root = '/content/drive/MyDrive/MyProject/whisper'
        # 簡單檢查掛載
        if not os.path.exists('/content/drive'):
            print("⚠️ Colab 環境但未檢測到 Drive，請確保已執行 drive.mount()")
        return root
    else:
        # 本地路徑
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))