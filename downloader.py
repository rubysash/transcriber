#!/usr/bin/env python3
"""
YouTube audio/video downloader module
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
        safe = "video"
    return safe

def download_media(url, output_dir, type="audio"):
    """
    Download media from URL
    type: "audio" or "video"
    """
    logger.section(f"STARTING {type.upper()} DOWNLOAD")
    logger.debug(f"URL: {url}")
    
    try:
        import yt_dlp

        # Extract info
        logger.debug("Extracting video info")
        ydl_opts_info = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id', 'temp')
            title = info.get('title', 'unknown')
            
        safe_title = sanitize_filename(title)
        
        if type == "audio":
            output_path_base = output_dir / f"audio_{video_id}"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_path_base),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            suffix = ".mp3"
        else:
            # Video: best quality with audio merged
            output_path_base = output_dir / f"{safe_title}_{video_id}"
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': str(output_path_base) + ".%(ext)s",
                'merge_output_format': 'mp4',
            }
            suffix = ".mp4"

        logger.debug(f"Starting {type} download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the file
        if type == "audio":
            final_file = output_path_base.with_suffix(suffix)
        else:
            # For video, it might have added .mp4 automatically
            final_file = Path(str(output_path_base) + suffix)
            if not final_file.exists():
                # Search for any file starting with title_id
                matches = list(output_dir.glob(f"{safe_title}_{video_id}.*"))
                if matches: final_file = matches[0]

        if not final_file.exists():
            raise FileNotFoundError(f"Media file not found after download: {final_file}")

        logger.success(f"Downloaded: {final_file.name}")
        return final_file, title

    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

def download_audio(url, output_dir):
    """Legacy wrapper for audio"""
    return download_media(url, output_dir, type="audio")

def cleanup_audio(audio_file):
    """Delete temporary audio file"""
    try:
        if audio_file.exists():
            audio_file.unlink()
            logger.debug("Deleted temporary file")
    except: pass
