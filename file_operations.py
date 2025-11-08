#!/usr/bin/env python3
"""
File operations for saving transcripts
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

def save_transcript(transcript, title, output_dir):
    """Save transcript to file"""
    logger.section("SAVING TRANSCRIPT")
    
    try:
        safe_name = sanitize_filename(title)
        output_file = output_dir / f"{safe_name}.txt"
        
        # Avoid overwriting
        counter = 1
        while output_file.exists():
            logger.debug(f"File exists: {output_file}")
            output_file = output_dir / f"{safe_name}_{counter}.txt"
            counter += 1
        
        logger.debug(f"Saving to: {output_file}")
        
        # Add header
        content = f"Video: {title}\n"
        content += f"{'='*60}\n\n"
        content += transcript
        
        output_file.write_text(content, encoding='utf-8')
        
        file_size = output_file.stat().st_size / 1024
        logger.success(f"Transcript saved: {output_file} ({file_size:.1f} KB)")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")
        logger.debug(f"Traceback:\n{traceback.format_exc()}")
        raise