#!/usr/bin/env python3
"""
System checks for FFmpeg and Python dependencies
"""
import os
import sys
import subprocess
from pathlib import Path
from logger import get_logger
from config import FFMPEG_PATH

logger = get_logger()

def check_ffmpeg():
    """Verify FFmpeg is available"""
    logger.debug("Checking FFmpeg availability")
    
    # Add to PATH if on Windows
    if os.name == 'nt':
        logger.debug(f"Windows detected, FFmpeg path: {FFMPEG_PATH}")
        if FFMPEG_PATH not in os.environ["PATH"]:
            logger.debug("Adding FFmpeg to PATH")
            os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ["PATH"]
        
        # Check if ffmpeg.exe exists
        ffmpeg_exe = Path(FFMPEG_PATH) / "ffmpeg.exe"
        logger.debug(f"Looking for ffmpeg.exe at: {ffmpeg_exe}")
        if not ffmpeg_exe.exists():
            logger.error(f"ffmpeg.exe not found at {ffmpeg_exe}")
            return False
        logger.debug("ffmpeg.exe found")
    
    # Try to run ffmpeg
    try:
        logger.debug("Testing FFmpeg command")
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        logger.debug(f"FFmpeg return code: {result.returncode}")
        
        if result.returncode == 0:
            version_line = result.stdout.decode().split('\n')[0]
            logger.success(f"FFmpeg found: {version_line}")
            return True
        
        logger.error("FFmpeg returned non-zero exit code")
        return False
        
    except FileNotFoundError:
        logger.error("FFmpeg command not found in PATH")
        return False
    except Exception as e:
        logger.error(f"FFmpeg check failed: {e}")
        return False

def check_dependencies():
    """Check all required Python packages"""
    logger.debug("Checking Python dependencies")
    
    missing = []
    versions = {}
    
    # Check yt-dlp
    logger.debug("Checking yt-dlp...")
    try:
        import yt_dlp
        version = yt_dlp.version.__version__
        versions['yt-dlp'] = version
        logger.success(f"yt-dlp version: {version}")
    except ImportError as e:
        logger.error("yt-dlp not found")
        missing.append("yt-dlp")
        logger.debug(f"Import error: {e}")
    
    # Check torch
    logger.debug("Checking torch...")
    try:
        import torch
        version = torch.__version__
        versions['torch'] = version
        logger.success(f"torch version: {version}")
    except ImportError as e:
        logger.error("torch not found")
        missing.append("torch")
        logger.debug(f"Import error: {e}")
    
    # Check faster-whisper
    logger.debug("Checking faster-whisper...")
    try:
        from faster_whisper import WhisperModel
        versions['faster-whisper'] = "installed"
        logger.success("faster-whisper found")
    except ImportError as e:
        logger.error("faster-whisper not found")
        missing.append("faster-whisper")
        logger.debug(f"Import error: {e}")
    
    if missing:
        logger.error("\nMissing packages:")
        for pkg in missing:
            logger.error(f"  pip install {pkg}")
        return False, None
    
    logger.success("All dependencies found!")
    return True, versions

def run_all_checks():
    """Run all system checks"""
    logger.section("RUNNING SYSTEM CHECKS")
    
    # Check FFmpeg
    logger.info("Step 1/2: Checking FFmpeg...")
    if not check_ffmpeg():
        logger.error("FFmpeg check FAILED")
        return False
    logger.success("FFmpeg check PASSED")
    
    # Check dependencies
    logger.info("\nStep 2/2: Checking Python dependencies...")
    success, versions = check_dependencies()
    if not success:
        logger.error("Dependencies check FAILED")
        return False
    logger.success("Dependencies check PASSED")
    
    logger.section("ALL SYSTEM CHECKS PASSED")
    return True