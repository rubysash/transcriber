#!/usr/bin/env python3
"""
YouTube audio downloader module
"""
import traceback
from pathlib import Path
from logger import get_logger

logger = get_logger()

def sanitize_filename(title):
    """Create safe filename from video title"""
    logger.debug(f"Sanitizing filename: {title}")
    safe = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    safe = safe.strip()[:100]
    if not safe:
        safe = "transcript"
    logger.debug(f"Sanitized to: {safe}")
    return safe

def download_audio(url, output_dir):
    """Download audio from YouTube URL"""
    logger.section("STARTING AUDIO DOWNLOAD")
    logger.debug(f"URL: {url}")
    logger.debug(f"Output directory: {output_dir}")
    
    try:
        import yt_dlp
        
        output_path = output_dir / "temp_audio"
        logger.debug(f"Output template: {output_path}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(output_path),
            'quiet': False,  # Show yt-dlp output for debugging
            'no_warnings': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        logger.debug("Creating YoutubeDL instance")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.debug("Extracting video info")
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown')
            duration = info.get('duration', 0)
            logger.info(f"Video: {title}")
            logger.info(f"Duration: {duration/60:.1f} minutes")
            
            logger.debug("Starting download")
            ydl.download([url])
        
        logger.debug("Download command completed")
        
        # Find the downloaded file
        logger.debug("Looking for downloaded audio file")
        audio_file = output_path.with_suffix('.mp3')
        logger.debug(f"Expected file: {audio_file}")
        
        if not audio_file.exists():
            logger.debug("Expected file not found, searching directory")
            files = list(output_dir.glob('temp_audio.*'))
            logger.debug(f"Found files: {files}")
            if files:
                audio_file = files[0]
                logger.debug(f"Using: {audio_file}")
            else:
                logger.error("No audio file found!")
                logger.debug(f"Directory contents: {list(output_dir.iterdir())}")
                raise FileNotFoundError("Audio file not found after download")
        
        file_size = audio_file.stat().st_size / (1024 * 1024)
        logger.success(f"Downloaded: {audio_file.name} ({file_size:.1f} MB)")
        
        return audio_file, title
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        raise

def cleanup_audio(audio_file):
    """Delete temporary audio file"""
    logger.debug(f"Cleaning up audio file: {audio_file}")
    try:
        if audio_file.exists():
            audio_file.unlink()
            logger.success("Audio file deleted")
        else:
            logger.debug("Audio file already deleted or not found")
    except Exception as e:
        logger.error(f"Failed to delete audio file: {e}")
        logger.debug(f"Traceback:\n{traceback.format_exc()}")