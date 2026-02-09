import os
import time
import json
from faster_whisper import WhisperModel
from typing import Optional

class PodcastTranscriber:
    def __init__(self, model_size: str = "medium", device: str = "auto", compute_type: str = "int8"):
        """
        初始化轉錄器
        :param model_size: 模型大小 (建議用 large-v3 以獲得最佳中文效果)
        :param device: "cpu" 或 "cuda" (您的筆電會自動選 cpu)
        :param compute_type: "int8" (省記憶體關鍵)
        """
        print(f"正在載入 Whisper 模型: {model_size} ({device})...")
        print("如果是第一次執行，會自動下載約 3GB 的模型檔，請耐心等候...")
        
        # 載入模型
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("✅ 模型載入完成！")

    def transcribe_file(self, audio_path: str) -> Optional[str]:
        """
        轉錄單個音訊檔案，輸出 txt 和 json
        """
        if not os.path.exists(audio_path):
            print(f"❌ 錯誤：找不到檔案 {audio_path}")
            return None

        file_name = os.path.basename(audio_path)
        print(f"\n🎙️ 開始轉錄: {file_name}")
        start_time = time.time()

        try:
            # --- 1. 執行轉錄 ---
            # language="zh": 強制指定中文
            # beam_size=5: 這是官方建議的最佳參數，搜尋最準確的句子
            # vad_filter=True: 過濾無聲片段
            segments, info = self.model.transcribe(
                audio_path, 
                beam_size=5, 
                language="zh", 
                vad_filter=True
            )

            print(f"   ℹ️ 偵測語言: {info.language} (信心度: {info.language_probability:.2f})")
            print(f"   ℹ️ 音訊長度: {info.duration:.2f} 秒")
            print("   ⏳ 轉錄中 (請稍候，長音檔會跑比較久)...")

            # --- 2. 準備輸出 ---
            # 建立 output 資料夾 (如果沒有的話)
            output_dir = os.path.join(os.path.dirname(audio_path), "../transcripts")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            base_name = os.path.splitext(file_name)[0]
            txt_path = os.path.join(output_dir, f"{base_name}.txt")
            json_path = os.path.join(output_dir, f"{base_name}.json")

            # 用來收集所有段落的清單 (給 JSON 用)
            transcript_data = []

            # --- 3. 寫入檔案 (即時寫入 TXT) ---
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"來源檔案: {file_name}\n")
                f.write(f"模型版本: large-v3\n")
                f.write("-" * 50 + "\n\n")

                # segments 是一個 Generator，這裡開始跑迴圈才會真正開始運算
                for i, segment in enumerate(segments, 1):
                    # 時間格式化 [MM:SS]
                    start_m, start_s = divmod(int(segment.start), 60)
                    end_m, end_s = divmod(int(segment.end), 60)
                    time_str = f"[{start_m:02d}:{start_s:02d} -> {end_m:02d}:{end_s:02d}]"
                    
                    # 組合文字
                    text = segment.text.strip()
                    line = f"{time_str} {text}"
                    
                    # 1. 寫入 TXT
                    f.write(line + "\n")
                    
                    # 2. 存入記憶體 (給 JSON)
                    transcript_data.append({
                        "id": i,
                        "start": segment.start,
                        "end": segment.end,
                        "text": text
                    })

                    # 3. 每轉錄 10 句在終端機印一次 (避免洗版，也讓你知道它還活著)
                    if i % 10 == 0:
                        print(f"   -> 已處理到: {time_str}")

            # --- 4. 寫入 JSON (結構化資料) ---
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)

            duration = time.time() - start_time
            print(f"\n✅ 轉錄完成！耗時: {duration:.2f} 秒")
            print(f"📄 文字檔: {txt_path}")
            print(f"📊 數據檔: {json_path}")
            return txt_path

        except Exception as e:
            print(f"❌ 轉錄失敗: {e}")
            return None

# --- 測試區 ---
if __name__ == "__main__":
    # 使用 medium 模型 (第一次執行會下載)
    # 您的 CPU (Ryzen AI 9) 絕對跑得動 int8 量化版
    transcriber = PodcastTranscriber(model_size="small", device="cpu", compute_type="int8")
    
    # 請修改這裡：填入您剛剛下載的「歐本豪斯」音檔檔名
    # 建議先用剛剛下載好的那個 mp3 來測
    # 假設檔案在 data/audio/
    
    # 這裡教您一個小技巧：自動抓 data/audio 資料夾裡最新的一個 mp3
    audio_dir = "data/audio/openhouse"
    if os.path.exists(audio_dir):
        files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.m4a'))]
        if files:
            # 找最新的檔案
            latest_file = max(files, key=os.path.getctime)
            transcriber.transcribe_file(latest_file)
        else:
            print(f"{audio_dir} 資料夾是空的，請先執行 rss_parser.py 下載音檔。")
    else:
        print(f"找不到 {audio_dir} 資料夾。")