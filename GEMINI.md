# YouTube Transcriber Project Context

This project is a modular Python-based tool for transcribing audio from YouTube videos, 900+ other websites (via `yt-dlp`), and local media files using OpenAI's Whisper model (implemented via `faster-whisper`).

## Project Overview

- **Core Technology:** Python 3.8+, `faster-whisper` (for transcription), `yt-dlp` (for downloading), `FFmpeg` (for audio processing), `PyQt5` (for GUI).
- **Architecture:** 
  - `main_gui.py`: Primary GUI entry point.
  - `main_cli.py`: Command-line interface entry point.
  - `transcriber.py`: Core transcription logic using `WhisperModel`.
  - `downloader.py`: Handles downloading and extracting audio from URLs.
  - `system_checks.py`: Validates FFmpeg and Python dependency availability.
  - `config.py`: Centralized configuration for paths, model sizes, and defaults.
  - `file_operations.py`: Helpers for saving transcripts and handling file system tasks.
  - `logger.py`: Custom logging utility for consistent console and file output.

## Building and Running

### Prerequisites

1.  **Python 3.8+**
2.  **FFmpeg:**
    - **Windows:** Expected at `C:\ffmpeg\bin` by default (configurable in `config.py`).
    - **Linux/Mac:** Should be available in the system PATH.
3.  **Virtual Environment (Recommended):**
    ```powershell
    python -m venv .
    .\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

### Execution

- **GUI Mode:**
  ```powershell
  python main_gui.py
  ```
- **CLI Mode:**
  ```powershell
  python main_cli.py [URL]
  ```
  *(If no URL is provided, it uses the default in `config.py`.)*

### Testing & Validation

The project uses `system_checks.py` to verify the environment at runtime.
- Run `python main_cli.py` to perform a quick end-to-end check with the default URL.
- Logs are saved to `transcripts/transcriber.log` or `transcripts/transcriber_gui.log`.

## Development Conventions

- **Configuration:** Always use `config.py` for pathing and default settings. Avoid hardcoding strings in logic files.
- **Logging:** Use the `logger` module instead of `print()`. Use `logger.info`, `logger.error`, `logger.debug`, and `logger.section` for consistent formatting.
- **Modular Logic:**
  - Keep downloading logic in `downloader.py`.
  - Keep transcription logic in `transcriber.py`.
  - Ensure all new features are accessible via both GUI and CLI where appropriate.
- **Error Handling:** Use specific try-except blocks, especially around I/O and network operations. Clean up temporary files (like `.mp3` downloads) using `cleanup_audio` from `downloader.py`.
- **Dependencies:** If adding new packages, update `requirements.txt`. Note that `torch` and `faster-whisper` are the primary heavy dependencies.

## Key Files

- `config.py`: Edit this to change the Whisper model size (`tiny` to `large`) or FFmpeg path.
- `requirements.txt`: Project dependencies.
- `transcripts/`: Default directory for all saved transcripts and logs.
- `start.bat`: Windows shortcut to activate venv and run the GUI.
