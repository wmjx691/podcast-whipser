import os
import yt_dlp

class YouTubeDownloader:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        # 🌟 對齊 RSSDownloader 的目錄檢查邏輯
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📂 建立目錄: {self.output_dir}")
        else:
            print(f"📂 下載目錄: {self.output_dir}")

    # 🌟 修改：加入 completed_bases 參數來接收情報局黑名單
    def download_audio(self, url: str, completed_bases: set = None) -> list:
        if completed_bases is None:
            completed_bases = set()
            
        print(f"🎬 準備從 YouTube 取得資訊: {url}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 1. 取得影片資訊 (先不下載)
                info_dict = ydl.extract_info(url, download=False)
                
                # 🌟 核心防呆：讓 yt-dlp 模擬產出最終的檔案路徑，我們藉此取得「安全檔名」
                expected_filepath = ydl.prepare_filename(info_dict)
                # 取得檔名 (不含路徑) 並去掉副檔名
                base_name = os.path.splitext(os.path.basename(expected_filepath))[0]
                
                # 2. 精準比對黑名單
                if base_name in completed_bases:
                    print(f"⏭️  情報顯示已完成轉錄，攔截下載: {base_name}")
                    return []
                
                # 3. 確認沒抓過，才真正執行下載
                print(f"⬇️  尚未轉錄過，開始下載音檔: {base_name}")
                ydl.download([url])
                
                final_filename = f"{base_name}.mp3"
                print(f"✅ YouTube 音檔下載完成: {final_filename}")
                return [final_filename]
                
        except Exception as e:
            print(f"❌ YouTube 下載失敗: {e}")
            return []