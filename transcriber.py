#!/usr/bin/env python3
"""
Audio transcription module using Whisper
"""
import traceback
from datetime import timedelta
from logger import get_logger
from config import DEVICE, COMPUTE_TYPE, BEAM_SIZE, VAD_FILTER, LANGUAGE

logger = get_logger()

def transcribe_audio(audio_file, model_size="tiny", include_timestamps=True):
    """Transcribe audio file using Whisper"""
    logger.section("STARTING TRANSCRIPTION")
    logger.debug(f"Audio file: {audio_file}")
    logger.debug(f"Model size: {model_size}")
    logger.debug(f"Include timestamps: {include_timestamps}")
    
    try:
        # Step 1: Import
        logger.debug("Step 1: Importing faster_whisper.WhisperModel")
        try:
            from faster_whisper import WhisperModel
            logger.debug("Step 1: Import successful")
        except ImportError as e:
            logger.error(f"Failed to import faster_whisper: {e}")
            raise
        
        # Step 2: Load model
        logger.info(f"Loading Whisper model ({model_size})...")
        logger.debug("This may take a moment on first run (downloading model)")
        logger.debug(f"Step 2: Loading Whisper model: {model_size}")
        logger.debug(f"Device: {DEVICE}, Compute type: {COMPUTE_TYPE}")
        
        try:
            logger.debug("Step 3: Creating WhisperModel instance...")
            
            # Add explicit error handling for common issues
            import os
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            # Create model with explicit parameters
            model = WhisperModel(
                model_size,
                device=DEVICE,
                compute_type=COMPUTE_TYPE,
                num_workers=1,  # Limit workers for thread safety
                download_root=None,  # Use default cache
            )
            logger.debug("Step 4: WhisperModel instance created successfully")
            logger.success("Model loaded!")
        except MemoryError as e:
            logger.error(f"Out of memory while creating WhisperModel: {e}")
            logger.error("Try closing other applications or using a smaller model")
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error creating WhisperModel: {e}")
            logger.error("This may be a library compatibility issue")
            logger.debug(f"Exception type: {type(e).__name__}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            raise
        except Exception as e:
            logger.error(f"Failed to create WhisperModel: {e}")
            logger.debug(f"Exception type: {type(e).__name__}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            raise
        
        # Step 3: Transcribe
        logger.debug("Step 5: Starting transcription...")
        logger.info("This may take a few minutes depending on audio length")
        
        try:
            logger.debug("Step 6: Calling model.transcribe()")
            segments, info = model.transcribe(
                str(audio_file),
                beam_size=BEAM_SIZE,
                language=LANGUAGE,
                vad_filter=VAD_FILTER,
            )
            logger.debug("Step 7: model.transcribe() returned successfully")
        except Exception as e:
            logger.error(f"model.transcribe() failed: {e}")
            logger.debug(f"Exception type: {type(e).__name__}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            raise
        
        logger.debug(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
        logger.debug(f"Audio duration: {info.duration:.1f}s")
        logger.success("Transcription started, processing segments")
        
        # Step 4: Process segments
        logger.debug("Step 8: Processing segments...")
        lines = []
        segment_count = 0
        last_reported = 0
        
        try:
            for segment in segments:
                segment_count += 1
                
                # Report progress every 10 segments
                if segment_count - last_reported >= 10:
                    logger.debug(f"Processed {segment_count} segments...")
                    last_reported = segment_count
                
                # Format with or without timestamp
                if include_timestamps:
                    ts = str(timedelta(seconds=int(segment.start)))
                    text = segment.text.strip()
                    lines.append(f"[{ts}] {text}")
                else:
                    text = segment.text.strip()
                    lines.append(text)
            
            logger.debug("Step 9: Segment processing completed")
        except Exception as e:
            logger.error(f"Error processing segments: {e}")
            logger.debug(f"Exception type: {type(e).__name__}")
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            raise
        
        logger.success(f"Processed {segment_count} total segments")
        
        if not lines:
            logger.error("No segments were transcribed!")
            return None
        
        transcript = "\n".join(lines)
        logger.debug(f"Transcript length: {len(transcript)} characters")
        logger.success("Transcription complete!")
        
        return transcript
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        raise