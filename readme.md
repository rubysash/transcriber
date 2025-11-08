# YouTube Video Transcriber

Transcribe videos from YouTube, Vimeo, 900+ sites, or local files using OpenAI's Whisper.

I absolutely HATE watching videos "Hey guys, what's up, smash the like, here is my dog, etc". 

This was created to extract the transcripts, so I can then parse it through AI for the juicy bits.

`Summarize this transcript into things I should know, or do to be better at this topic:`

## Features

- YouTube, Vimeo, and 900+ video sites via yt-dlp
- Local video/audio file support (MP4, MP3, WAV, etc.)
- Multiple Whisper model sizes (tiny to large)
- Dark theme GUI
- Auto-saves transcripts to `/transcripts/` folder
- Auto-copies to clipboard
- Optionally rip out the mp3 of the audio if desired.

## Installation

### 1. Clone Repository
```bash
git clone [https://github.com/rubysash/transcriber.git](https://github.com/rubysash/transcriber.git)
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv transcriber
cd transcriber
Scripts\activate

# Linux/Mac
python3 -m venv transcriber
cd transcriber
source bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg\`
3. Or edit `config.py` with your FFmpeg path

**Linux:**
```bash
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

## Usage

```bash
python main_gui.py
```

1. Enter YouTube URL or click **Browse** for local file
2. Select model size (tiny/base/small/medium/large)
3. Click **Start Transcription**
4. Transcript auto-saves to `transcripts/` folder and copies to clipboard

## Configuration

Edit `config.py`:
```python
# FFmpeg path (Windows only)
FFMPEG_PATH = r"C:\ffmpeg\bin"

# Default model
DEFAULT_MODEL_SIZE = "tiny"

# Debug logging (True = verbose, False = quiet)
DEBUG_MODE = False
```

## Model Sizes

Models download automatically on first use and are cached.

| Model | Size | Speed | Accuracy | First Download |
|-------|------|-------|----------|----------------|
| **tiny** | ~75MB | Fast | Good | 10-30 seconds |
| **base** | ~150MB | Fast | Better | 30-60 seconds |
| **small** | ~500MB | Medium | Great | 1-2 minutes |
| **medium** | ~1.5GB | Slow | Excellent | 2-5 minutes |
| **large** | ~3GB | Very Slow | Best | 5-10 minutes |

**Recommendation:** Start with `tiny` for testing, use `medium` for production.

## Model Quality Example

Same audio transcribed with different models:

### Tiny Model (~75MB, 2 minutes)
```
[0:01:00] What happens though is people say they don't need me motivation 
and I say well that's interesting. That's not what I do. I'm the [wide] guy.
[0:01:41] But we all know that that's bullshit at times you don't work in 
[yourself] interest all the time
```
*Errors: "wide" → "why", "yourself" → "your self"*

### Medium Model (~1.5GB, several minutes)
```
[0:01:01] What happens though is people say to me, I don't need any motivation.
[0:01:04] I say, well that's interesting, that's not what I do.
[0:01:06] I'm the why guy.
[0:01:42] We all know that that's bullshit at times.
[0:01:45] You don't work in your self interest all the time.
```
*Accurate words, better punctuation, precise timing*

## Supported Sites

Via yt-dlp: YouTube, Vimeo, Twitter/X, Reddit, Facebook, TikTok, Twitch, and 890+ more.

## Output

Transcripts save to `transcripts/` folder:
```
transcripts/
├── Video Title.txt
├── Video Title_1.txt  (if duplicate)
└── transcriber_gui.log
```

## Troubleshooting

**"FFmpeg not found"**
- Windows: Check `FFMPEG_PATH` in `config.py`
- Linux/Mac: Run `ffmpeg -version`

**"Module not found"**
```bash
pip install -r requirements.txt
```

**Model download fails**
- Check internet connection
- Delete `~/.cache/huggingface/hub/` and retry

**Poor transcription quality**
- Use larger model (medium or large)
- Ensure clear audio in source

**Too much debug output**
- Set `DEBUG_MODE = False` in `config.py`

## Requirements

- Python 3.8+
- 4GB+ RAM (8GB+ for medium/large models)
- FFmpeg

- Internet connection
