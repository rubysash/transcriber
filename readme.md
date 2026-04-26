# Media Downloader & Transcriber

**Warning:** Using larger Whisper models (medium/large) requires 4GB to 8GB of disk space and significant RAM. The "tiny" model is fast (~75MB) and good for testing, while "medium" is recommended for high-quality production transcripts.

Transcribe audio or download video from YouTube, Vimeo, and 900+ other sites using OpenAI's Whisper and yt-dlp.

## Features

- **Multi-Source Support:** YouTube, Vimeo, Twitter/X, TikTok, and 900+ more via yt-dlp.
- **Audio & Video Downloads:** Choose to download just the MP3 audio or the full MP4 video.
- **Skip Transcription Mode:** Use as a standalone downloader to quickly grab media without running AI models.
- **Background Processing:** The GUI remains fully responsive while downloading and transcribing.
- **Unique File Naming:** Automatically uses video IDs in temporary filenames to prevent collisions.
- **Multiple Whisper Models:** Supports `tiny`, `base`, `small`, `medium`, and `large` models.
- **Auto-Save & Clipboard:** Transcripts are auto-saved to the `transcripts/` folder and copied to your clipboard.

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/rubysash/transcriber.git
cd transcriber
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .
Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Linux/Mac
python3 -m venv .
source bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install FFmpeg

**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html).
2. Extract to `C:\ffmpeg\bin`.
3. Verify or edit `FFMPEG_PATH` in `config.py`.

**Linux:** `sudo apt install ffmpeg`  
**Mac:** `brew install ffmpeg`

## Usage

### GUI Mode (Recommended)
```bash
python main_gui.py
```
1. Enter a URL or **Browse** for a local file.
2. Select **Download Type** (audio/video).
3. Select **Whisper Model** (ignored if skipping transcription).
4. Check **Skip Transcription** if you only want to download the file.
5. Click **Run Task**.

### CLI Mode
```bash
python main_cli.py [URL]
```

## Configuration

Edit `config.py` to change defaults:
- `FFMPEG_PATH`: Path to your FFmpeg binaries.
- `DEFAULT_MODEL_SIZE`: Default Whisper model to use.
- `DEVICE`: Set to `"cpu"` or `"cuda"` (if you have an Nvidia GPU and CUDA installed).

## Troubleshooting

- **WinError 1114:** Ensure you have the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) installed. This is common on fresh Windows installs.
- **yt-dlp Errors:** Video sites frequently update their code. Run `pip install -U yt-dlp` to get the latest fix.
- **GUI Freezes:** Model download can be up to 8GB on the first run.   Subsequent runs of the same model should be fast.
- **Symlink Warnings:** On Windows, if you see warnings about symlinks, you can safely ignore them or enable "Developer Mode" in Windows settings.

## Requirements

- Tested on 3.13
- 4GB+ RAM (8GB+ recommended for larger models)
- FFmpeg installed and in PATH (or configured in `config.py`)
- Internet connection (for downloads and first-time model caching)
