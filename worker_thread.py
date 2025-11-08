#!/usr/bin/env python3
"""
Worker thread for non-blocking GUI transcription
"""
import traceback
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from logger import get_logger
from config import OUTPUT_DIR
from system_checks import check_ffmpeg, check_dependencies
from downloader import download_audio, cleanup_audio
from transcriber import transcribe_audio

logger = get_logger()

class TranscriberThread(QThread):
    """Worker thread for non-blocking transcription"""
    status_update = pyqtSignal(str, str)  # message, type (debug/error/success/info)
    progress_update = pyqtSignal(int)  # progress percentage
    finished_signal = pyqtSignal(str, str)  # transcript, title
    error_signal = pyqtSignal(str)
    
    def __init__(self, url, model_size, save_audio, include_timestamps):
        super().__init__()
        logger.debug("Initializing TranscriberThread")
        self.url = url
        self.model_size = model_size
        self.save_audio = save_audio
        self.include_timestamps = include_timestamps
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
        logger.debug(f"Output directory: {self.output_dir}")
        
    def emit_status(self, msg, msg_type="info"):
        """Emit status update to GUI and log"""
        # Log the message
        if msg_type == "debug":
            logger.debug(msg)
        elif msg_type == "error":
            logger.error(msg)
        elif msg_type == "success":
            logger.success(msg)
        else:
            logger.info(msg)
        
        # Emit to GUI
        self.status_update.emit(msg, msg_type)
        
    def run(self):
        """Main transcription process"""
        logger.section("WORKER THREAD STARTED")
        logger.debug(f"URL: {self.url}")
        logger.debug(f"Model: {self.model_size}")
        logger.debug(f"Save audio: {self.save_audio}")
        logger.debug(f"Include timestamps: {self.include_timestamps}")
        
        audio_file = None
        
        try:
            # Step 1: Check FFmpeg
            self.emit_status("Step 1/5: Checking FFmpeg...", "info")
            if not check_ffmpeg():
                logger.error("FFmpeg check FAILED")
                self.error_signal.emit("FFmpeg not found! Please install FFmpeg.")
                return
            logger.success("FFmpeg check PASSED")
            self.progress_update.emit(5)
            
            # Step 2: Check dependencies
            self.emit_status("Step 2/5: Checking dependencies...", "info")
            success, versions = check_dependencies()
            if not success:
                logger.error("Dependencies check FAILED")
                self.error_signal.emit("Missing dependencies! Install yt-dlp, torch, and faster-whisper.")
                return
            logger.success("Dependencies check PASSED")
            self.progress_update.emit(10)
            
            # Step 3: Download audio
            self.emit_status("Step 3/5: Downloading audio from YouTube...", "info")
            try:
                audio_file, title = download_audio(self.url, self.output_dir)
                logger.success(f"Download COMPLETE: {audio_file}")
                self.progress_update.emit(40)
            except Exception as e:
                logger.error(f"Download failed: {e}")
                raise
            
            # Step 4: Transcribe
            self.emit_status("Step 4/5: Transcribing audio (this may take a few minutes)...", "info")
            try:
                # Important: Transcription can take a long time and block the thread
                # The QThread should handle this, but we need to ensure it doesn't crash
                transcript = transcribe_audio(audio_file, self.model_size, self.include_timestamps)
                
                if not transcript:
                    raise Exception("Transcription produced no output")
                
                logger.success(f"Transcription COMPLETE: {len(transcript)} characters")
                self.progress_update.emit(90)
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                logger.debug(f"Transcription error traceback: {traceback.format_exc()}")
                raise
            
            # Step 5: Cleanup
            self.emit_status("Step 5/5: Finalizing...", "info")
            if not self.save_audio and audio_file:
                try:
                    cleanup_audio(audio_file)
                except Exception as e:
                    logger.warning(f"Cleanup failed: {e}")
            elif audio_file:
                self.emit_status(f"Audio saved: {audio_file.name}", "success")
            
            self.progress_update.emit(100)
            
            logger.section("TRANSCRIPTION COMPLETE!")
            self.finished_signal.emit(transcript, title)
            
        except KeyboardInterrupt:
            logger.warning("Worker thread interrupted by user")
            self.error_signal.emit("Process cancelled by user")
            
        except Exception as e:
            logger.section("EXCEPTION IN WORKER THREAD")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception message: {str(e)}")
            logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            
            # Cleanup on error
            if audio_file and audio_file.exists() and not self.save_audio:
                try:
                    cleanup_audio(audio_file)
                    logger.debug("Cleaned up audio file after error")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup audio: {cleanup_error}")
            
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.emit_status(f"Error: {error_msg}", "error")
            self.error_signal.emit(error_msg)