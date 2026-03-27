import os
import json
import re
from typing import Dict, Any
from googleapiclient.discovery import build
from upload_to_drive import get_oauth_credentials 

class IdempotencyChecker:
    # 🌟 修改：初始化時加入 podcast_name
    def __init__(self, audio_dir: str, transcript_dir: str, drive_folder_id: str, podcast_name: str):
        self.audio_dir = audio_dir
        self.transcript_dir = transcript_dir
        self.drive_folder_id = drive_folder_id
        self.podcast_name = podcast_name

    def check_local_audio(self) -> set:
        """任務 1: 檢查本地已下載的音檔"""
        existing_audio = set()
        if not os.path.exists(self.audio_dir):
            return existing_audio
        
        valid_exts = ('.mp3', '.m4a', '.wav', '.flac')
        for f in os.listdir(self.audio_dir):
            if f.lower().endswith(valid_exts):
                existing_audio.add(os.path.splitext(f)[0])
        return existing_audio

    def check_local_transcripts(self) -> Dict[str, Any]:
        """任務 2: 檢查本地已轉錄的 JSON 檔，並解析 metadata"""
        local_status = {}
        if not os.path.exists(self.transcript_dir):
            return local_status
        for f in os.listdir(self.transcript_dir):
            if f.endswith('.json'):
                base_name = os.path.splitext(f)[0]
                try:
                    with open(os.path.join(self.transcript_dir, f), 'r', encoding='utf-8') as file:
                        metadata = json.load(file).get("metadata", {})
                        local_status[base_name] = {
                            "location": "local",
                            "model_size": metadata.get("model_size", "unknown"),
                            "environment": metadata.get("environment", "unknown")
                        }
                except Exception:
                    pass
        return local_status

    # 🌟 新增：尋找對應節目子資料夾 ID 的方法
    def _get_drive_subfolder_id(self, service) -> str:
        query = f"'{self.drive_folder_id}' in parents and name='{self.podcast_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])
        return items[0]['id'] if items else None

    def check_drive_transcripts(self) -> Dict[str, Any]:
        """任務 3: 檢查 Google Drive 特定子資料夾上的檔案"""
        drive_status = {}
        if not self.drive_folder_id:
            return drive_status

        print("🔍 [情報局] 正在連接 Google Drive 獲取雲端情報...")
        try:
            creds = get_oauth_credentials()
            service = build('drive', 'v3', credentials=creds)
            
            # 🌟 修改：先找出目標節目的子資料夾 ID
            target_folder_id = self._get_drive_subfolder_id(service)
            if not target_folder_id:
                print(f"🔍 [情報局] 雲端尚未建立 {self.podcast_name} 的資料夾，視為全無歷史紀錄。")
                return drive_status

            # 只在找到的子資料夾內搜尋
            query = f"'{target_folder_id}' in parents and trashed=false"
            page_token = None
            
            while True:
                results = service.files().list(
                    q=query, 
                    fields="nextPageToken, files(id, name, appProperties)",
                    pageToken=page_token,
                    pageSize=1000
                ).execute()
                
                for item in results.get('files', []):
                    name = item.get('name', '')
                    # 同時尋找 txt 或 json，確保不會漏抓
                    if name.endswith('.json') or name.endswith('.txt'):
                        base_name = os.path.splitext(name)[0]
                        # appProperties 是 Google Drive 給開發者用的自訂標籤字典
                        props = item.get('appProperties', {})
						
                        # 如果同一個檔案有 txt 也有 json，我們保留 json 抓到的 metadata
                        if base_name not in drive_status or name.endswith('.json'):
                            drive_status[base_name] = {
                                "location": "drive",
                                "model_size": props.get("model_size", "unknown"),
                                "environment": props.get("environment", "unknown"),
                                "drive_id": item.get('id')
                            }
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break # 沒有下一頁了，跳出迴圈
        except Exception as e:
            print(f"⚠️ 無法取得雲端檔案清單: {e}")
        
        return drive_status

    def get_comprehensive_status(self) -> Dict[str, Dict]:
        """
        任務 4: 整合所有情報，回傳終極狀態字典給 main.py 使用。
        """
        print("\n📊 [情報局] 正在進行全盤狀態掃描...")
        local_audio = self.check_local_audio()
        local_transcripts = self.check_local_transcripts()
        drive_transcripts = self.check_drive_transcripts()

        # 把所有出現過的檔名收集成一個大聯集 (Union)
        all_bases = set(local_audio) | set(local_transcripts.keys()) | set(drive_transcripts.keys())
        
        comprehensive_status = {}
        unique_eps = set()
        ghost_files = [] 
        
        for base in all_bases:
            status = {
                "has_audio": base in local_audio,
                "transcript": None 
            }
            # 決定逐字稿的最終狀態 (雲端優先於本地)
            if base in drive_transcripts:
                status["transcript"] = drive_transcripts[base]
            elif base in local_transcripts:
                status["transcript"] = local_transcripts[base]
            comprehensive_status[base] = status
            
            # --- 萃取 EP 數字，還原真實集數 ---
            ep_match = re.search(r"(?i)EP\.?\s*(\d+)", base)
            if ep_match:
                # 如果是 EP 開頭，就抽出數字 (例如 EP438 和 EP438_new 都會變成 438)
                # set 會自動把重複的 438 融合為 1 個
                unique_eps.add(int(ep_match.group(1)))
            else:
                # 找不到 EP 號碼，列入幽靈名單
                ghost_files.append(base)
                unique_eps.add(base) 
            
        print(f"✅ 情報掃描完成！共發現 {len(unique_eps)} 集 {self.podcast_name} 節目的紀錄。")
        # 印出抓鬼名單，讓您知道是誰搞鬼
        if ghost_files:
            print(f"👻 注意：發現 {len(ghost_files)} 個無法辨識集數的幽靈檔案:")
            for ghost in ghost_files:
                print(f"   - {ghost}")
            
        return comprehensive_status