# Auto Podcast Transcriber & Cloud Archiver 🎙️ -> 📝 -> ☁️

![Python](https://img.shields.io/badge/Python-3.10-blue)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-success)
![Whisper](https://img.shields.io/badge/AI%20Model-faster--whisper-orange)
![Google Drive API](https://img.shields.io/badge/Google%20API-OAuth%202.0-yellow)

An end-to-end automated data pipeline that periodically downloads specific podcast episodes (e.g., discussions on real estate and urban development), transcribes the audio into text using AI, and securely archives the transcripts to Google Drive.

## 🌟 Key Features

* **Fully Automated CI/CD Pipeline:** Scheduled via GitHub Actions to run automatically twice a week. No manual intervention required.
* **Smart Idempotency:** Implements checks against the Google Drive API before uploading, preventing duplicate file uploads and saving bandwidth/API quota.
* **AI-Powered Transcription:** Utilizes `faster-whisper` for highly accurate, offline speech-to-text conversion.
* **Secure Authentication:** Integrates Google Drive API via OAuth 2.0. Sensitive credentials and tokens are strictly protected using GitHub Secrets and environment variables.

## 🏗️ System Architecture

1. **RSS Parsing (`src/rss_parser.py`):** Fetches the latest episodes from the target podcast RSS feed and downloads the audio files.
2. **Audio Transcription (`src/transcriber.py`):** Processes the downloaded audio using the Whisper model, converting Taiwanese/Mandarin speech into Traditional Chinese transcripts (.txt & .json).
3. **Cloud Upload (`src/upload_to_drive.py`):** Authenticates via Google OAuth 2.0 and uploads the generated transcripts directly to a designated Google Drive folder.
4. **Automation (`main.py` & `.github/workflows/podcast_auto.yml`):** The main controller script triggered by GitHub Actions.

## 🛠️ Tech Stack

- **Language**: Python 3.10
- **AI Model:** [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper V3)
- **APIs:** Google Drive API v3 (OAuth 2.0)
- **Tools & Libraries:** `feedparser`, `requests`, `google-auth-oauthlib`, `tqdm`
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
Run the main script to start the pipeline:
```bash
python main.py
```
(Note: The first run will open a browser window for Google OAuth authorization. A `token.json` will be generated for subsequent automated runs.)
