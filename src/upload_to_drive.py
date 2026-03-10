import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- 1. 環境與路徑設定 ---
def detect_environment():
    return "COLAB_RELEASE_TAG" in os.environ or 'google.colab' in sys.modules

def get_project_root():
    if detect_environment():
        return '/content/drive/MyDrive/MyProject/whisper'
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 只請求 Google Drive 的檔案建立權限
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# --- 2. OAuth 2.0 驗證邏輯 ---
def get_oauth_credentials():
    project_root = get_project_root()
    token_path = os.path.join(project_root, 'token.json')
    client_secret_path = os.path.join(project_root, 'client_secret.json')
    
    creds = None
    # 如果之前已經登入過，就會有 token.json
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # 如果沒有憑證，或是憑證過期了，就執行登入流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 憑證已過期，正在自動刷新...")
            creds.refresh(Request())
        else:
            print("🌐 準備開啟瀏覽器進行 Google 授權登入...")
            if not os.path.exists(client_secret_path):
                raise FileNotFoundError(f"❌ 找不到 {client_secret_path}，請確認是否已下載 OAuth 憑證！")
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            # 加入 open_browser=False，並指定一個固定 port (例如 8080)
            print("請複製下方的網址，貼到您電腦的瀏覽器中開啟並完成授權：")
            creds = flow.run_local_server(port=8080, open_browser=False, bind_addr='127.0.0.1')
            
        # 把拿到的授權存進 token.json，下次就不用再開網頁登入了！
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    return creds

# --- 3. Google Drive 上傳邏輯 ---
def upload_files_to_drive(folder_id: str, target_dir: str = None):
    if target_dir is None:
        project_root = get_project_root()
        transcripts_dir = os.path.join(project_root, "data", "transcripts")
    else:
        transcripts_dir = target_dir
        
    if not os.path.exists(transcripts_dir):
        print(f"❌ 找不到轉錄檔資料夾: {transcripts_dir}")
        return

    print("🔑 正在驗證 OAuth 權限...")
    try:
        creds = get_oauth_credentials()
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ API 驗證失敗: {e}")
        return

    # --- 🌟 新增：取得雲端硬碟目標資料夾內已有的檔案清單 ---
    print(f"🔍 正在檢查雲端資料夾內已存在的檔案...")
    existing_file_names = set()
    try:
        # 使用 q 語法查詢該 folder_id 底下且未被丟入垃圾桶的檔案
        query = f"'{folder_id}' in parents and trashed=false"
        # 執行查詢，我們只需要檔案的 id 和 name
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        for item in items:
            existing_file_names.add(item['name'])
            
    except Exception as e:
        print(f"⚠️ 無法取得雲端檔案清單，將執行全量上傳。錯誤: {e}")
    # -----------------------------------------------------

    files_to_upload = [f for f in os.listdir(transcripts_dir) if f.endswith(('.txt', '.json'))]
    if not files_to_upload:
        print("⚠️ 沒有找到任何 .txt 或 .json 檔案需要上傳。")
        return

    print(f"📂 準備比對並上傳 {len(files_to_upload)} 個檔案至 Google Drive...")

    for filename in files_to_upload:
        # --- 🌟 新增：過濾判斷式 ---
        if filename in existing_file_names:
            print(f"⏭️  雲端已存在，跳過上傳: {filename}")
            continue # 直接跳過這個檔案，進入下一個迴圈
        # ------------------------
        
        filepath = os.path.join(transcripts_dir, filename)
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        mimetype = 'application/json' if filename.endswith('.json') else 'text/plain'
        media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)

        print(f"⬆️  正在上傳: {filename} ...", end="", flush=True)
        try:
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f" ✅ 完成 (雲端 ID: {uploaded_file.get('id')})")
        except Exception as e:
            print(f" ❌ 失敗: {e}")