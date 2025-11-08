#!/usr/bin/env python3
"""
Simple CLI YouTube Transcriber - Modular Version
"""
import sys
from pathlib import Path

# Import our modules
from logger import get_logger
from config import DEFAULT_URL, OUTPUT_DIR, DEFAULT_MODEL_SIZE
from system_checks import run_all_checks
from downloader import download_audio, cleanup_audio
from transcriber import transcribe_audio
from file_operations import save_transcript

def main():
    """Main function"""
    # Setup logger
    log_file = OUTPUT_DIR / "transcriber.log"
    logger = get_logger(log_file)
    
    logger.section("YouTube Whisper Transcriber (CLI)")
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
        logger.info(f"Using URL from command line: {url}")
    else:
        url = DEFAULT_URL
        logger.info(f"Using default URL: {url}")
    
    # Setup output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    logger.debug(f"Output directory: {OUTPUT_DIR}")
    logger.debug(f"Working directory: {Path.cwd()}")
    logger.debug(f"Log file: {log_file}")
    
    # Check prerequisites
    logger.info("\n[1/5] Checking prerequisites...")
    if not run_all_checks():
        logger.error("\nPrerequisite checks failed!")
        return 1
    
    # Download audio
    logger.info("\n[2/5] Downloading audio...")
    try:
        audio_file, title = download_audio(url, OUTPUT_DIR)
    except Exception as e:
        logger.error(f"\nDownload failed: {e}")
        return 1
    
    # Transcribe
    logger.info("\n[3/5] Transcribing audio...")
    try:
        transcript = transcribe_audio(audio_file, DEFAULT_MODEL_SIZE)
        if not transcript:
            logger.error("Transcription produced no output!")
            cleanup_audio(audio_file)
            return 1
    except Exception as e:
        logger.error(f"\nTranscription failed: {e}")
        cleanup_audio(audio_file)
        return 1
    
    # Save transcript
    logger.info("\n[4/5] Saving transcript...")
    try:
        output_file = save_transcript(transcript, title, OUTPUT_DIR)
    except Exception as e:
        logger.error(f"\nSave failed: {e}")
        cleanup_audio(audio_file)
        return 1
    
    # Cleanup
    logger.info("\n[5/5] Cleaning up...")
    cleanup_audio(audio_file)
    
    # Success!
    logger.section("SUCCESS!")
    logger.info(f"Transcript saved to: {output_file}")
    logger.info(f"File size: {output_file.stat().st_size / 1024:.1f} KB")
    logger.info(f"Lines: {len(transcript.split(chr(10)))}")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger = get_logger()
        logger.error(f"\nUnexpected error: {e}")
        import traceback
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        sys.exit(1)