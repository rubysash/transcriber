#!/usr/bin/env python3
"""
Configuration settings for YouTube Transcriber
"""
from pathlib import Path

# FFmpeg Configuration
FFMPEG_PATH = r"C:\ffmpeg\bin"

# Default Settings
DEFAULT_URL = "https://www.youtube.com/watch?v=cjXp3bBd2h8"
DEFAULT_MODEL_SIZE = "tiny"
DEFAULT_SAVE_AUDIO = True
DEFAULT_INCLUDE_TIMESTAMPS = True

# Directory Configuration
OUTPUT_DIR = Path.cwd() / "transcripts"

# Model Settings
AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

# Transcription Settings
BEAM_SIZE = 1
VAD_FILTER = True
LANGUAGE = "en"


# Debug Verbosity
DEBUG_MODE = False  # Set to True for verbose logging, False for quiet operation