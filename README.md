# Auto Podcast Transcriber & Cloud Archiver 🎙️ -> 📝 -> ☁️

![Python](https://img.shields.io/badge/Python-3.10-blue)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-success)
![Whisper](https://img.shields.io/badge/AI%20Model-faster--whisper-orange)
![Google Drive API](https://img.shields.io/badge/Google%20API-OAuth%202.0-yellow)

An end-to-end automated data pipeline that periodically downloads specific podcast episodes (e.g., discussions on real estate, urban development, and stock market analysis), transcribes the audio into text using AI, and securely archives the transcripts to Google Drive.

## 🌟 Key Features (V2 Update)

* **Smart Idempotency (State-Aware):** Cross-references local storage and Google Drive (via `appProperties`) to prevent redundant downloads and duplicate uploads. It strictly filters by Episode (EP) numbers, saving bandwidth and API quotas.
* **Multi-Podcast & Dynamic Subfolders:** Automatically creates and routes files to specific subfolders in Google Drive (e.g., `openhouse`, `gooaye`) based on the target podcast, keeping your cloud storage perfectly organized.
* **Rich Metadata Embeds:** Generates structured `.json` files alongside `.txt` transcripts, embedding valuable metadata (model size, environment, prompt, timestamp) into both the file and Google Drive's hidden `appProperties`.
* **Dual-Track Execution:** Designed to run seamlessly as a fully automated CI/CD pipeline (via GitHub Actions) or as a high-performance GPU transcribing engine on Google Colab for private audio (e.g., interview recordings or bulk processing).
* **AI-Powered Transcription:** Utilizes `faster-whisper` for highly accurate, offline speech-to-text conversion supporting Mixed Taiwanese/Mandarin.

## 🏗️ System Architecture

1. **Intelligence / Idempotency (`src/idempotency_checker.py`):** Scans local and cloud states to generate an exact blacklist of processed episodes.
2. **RSS Parsing & Downloading (`src/rss_parser.py`):** Fetches the latest episodes from the target podcast RSS feed, skipping existing ones using the intelligence blacklist.
3. **Audio Transcription (`src/transcriber.py`):** Processes the downloaded audio using the Whisper model, generating text and metadata JSON.
4. **Smart Cloud Upload (`src/upload_to_drive.py`):** Authenticates via OAuth 2.0, creates podcast-specific subfolders, and applies metadata as cloud tags.
5. **Orchestrator (`main.py` & `.github/workflows/podcast_auto.yml`):** The central control script managing the entire workflow.

## 🛠️ Tech Stack

- **Language**: Python 3.10
- **AI Model:** [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper V3)
- **APIs:** Google Drive API v3 (OAuth 2.0)
- **Tools & Libraries:** `feedparser`, `requests`, `google-auth-oauthlib`, `tqdm`, `opencc`
- **DevOps:** GitHub Actions

## ⚙️ Local Setup & Usage

### Prerequisites
* Python 3.10+
* FFmpeg installed on your system
* Google Cloud Console project with Drive API enabled and OAuth 2.0 Client ID created.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/KevinYu/podcast-whisper.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Environment Setup:
   -  Place your `client_secret.json` in the root directory.
   -  Create a `.env` file in the root directory and add your Google Drive folder ID:
   ```Code
   DRIVE_FOLDER_ID=your_target_folder_id_here
   ```

### **Execution**
Before running, you can configure the target podcast and model size inside `main.py` (e.g., `TARGET_MODEL = "small"`, `PODCAST_NAME = "gooaye"`).

Run the main script to start the pipeline:
```bash
python main.py
```
(Note: The first run will open a browser window for Google OAuth authorization. A `token.json` will be generated for subsequent automated runs.)
