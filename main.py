from dotenv import load_dotenv
load_dotenv() # 這行會自動把 .env 裡面的東西載入到環境變數中
import os
import sys

# 將 src 目錄加入系統路徑，方便載入我們的模組
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from rss_parser import PodcastDownloader
from transcriber import PodcastTranscriber
from upload_to_drive import upload_files_to_drive, get_project_root

def main():
    print("========== 🚀 開始自動化 Podcast 轉錄流程 ==========")
    
    # --- 參數設定區 ---
    RSS_URL = "https://feed.firstory.me/rss/user/cke0tqspfvlc00803lwhmdb2t"
    PODCAST_NAME = "openhouse" # 資料夾名稱
    # 動態讀取環境變數的做法
    DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

    if not DRIVE_FOLDER_ID:
        raise ValueError("❌ 找不到 DRIVE_FOLDER_ID！請確保已設定環境變數。")
    
    # 1. 初始化路徑
    project_root = get_project_root()
    audio_dir = os.path.join(project_root, "data", "audio", PODCAST_NAME)
    transcript_dir = os.path.join(project_root, "data", "transcripts", PODCAST_NAME)
    credentials_path = os.path.join(project_root, "credentials.json")

    # --- 步驟一：下載最新音檔 ---
    print("\n>> [步驟 1/3]: 執行 RSS 檢查與音檔下載...")
    downloader = PodcastDownloader(RSS_URL, sub_dir=PODCAST_NAME)
    # 自動化時，我們只需要抓最新的一集即可
    downloader.download_recent_episodes(count=1) 

    # --- 步驟二：執行語音轉錄 ---
    print("\n>> [步驟 2/3]: 執行 Whisper 語音轉錄...")
    is_colab = "COLAB_RELEASE_TAG" in os.environ
    
    # 如果在 GitHub Actions (通常沒有 GPU) 跑，我們強制用 CPU 和 int8；若是 Colab 則用 GPU
    device = "cuda" if is_colab else "cpu"
    compute_type = "float16" if is_colab else "int8"
    
    transcriber = PodcastTranscriber(model_size="small", device=device, compute_type=compute_type)
    transcriber.transcribe_folder(
        folder_path=audio_dir,
        output_path=transcript_dir,
        language="zh",
        prompt="None"
    )

    # --- 步驟三：上傳至雲端硬碟 ---
    print("\n>> [步驟 3/3]: 上傳結果至 Google Drive...")
    # 注意：這裡我們需要稍微修改一下傳給 upload_files_to_drive 的邏輯
    # 讓它知道要上傳哪個資料夾的檔案
    upload_files_to_drive(DRIVE_FOLDER_ID, target_dir=transcript_dir)
    
    print("\n========== ✅ 自動化流程執行完畢！ ==========")

if __name__ == "__main__":
    main()