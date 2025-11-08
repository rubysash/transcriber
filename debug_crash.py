#!/usr/bin/env python3
"""
DEBUGGING GUIDE - Transcription Crash After Download

This script helps identify why the transcription fails after downloading audio.
"""

import sys
from pathlib import Path

print("="*60)
print("TRANSCRIPTION CRASH DEBUGGER")
print("="*60)
print()

# Test 1: Import faster_whisper
print("Test 1: Can we import faster_whisper?")
try:
    from faster_whisper import WhisperModel
    print("✓ SUCCESS: faster_whisper imported")
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Check for existing audio file
print("\nTest 2: Check for test audio file")
test_audio = Path("transcripts/temp_audio.mp3")
if test_audio.exists():
    print(f"✓ Found: {test_audio}")
    print(f"  Size: {test_audio.stat().st_size / (1024*1024):.1f} MB")
else:
    print("✗ No test audio file found")
    print(f"  Expected: {test_audio}")
    print("  Run the downloader first, then try again")
    sys.exit(1)

# Test 3: Create WhisperModel instance
print("\nTest 3: Can we create a WhisperModel instance?")
print("  This is where your crash likely occurs...")
print("  Model: tiny")
print("  Device: cpu")
print("  Compute type: int8")

try:
    print("\n  Creating model instance...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("✓ SUCCESS: WhisperModel created")
except MemoryError as e:
    print(f"✗ FAILED: Out of memory")
    print(f"  Error: {e}")
    print("\nSOLUTION:")
    print("  1. Close other applications")
    print("  2. Your system may not have enough RAM")
    print("  3. Try on a machine with more RAM")
    sys.exit(1)
except Exception as e:
    print(f"✗ FAILED: {e}")
    print(f"\nException type: {type(e).__name__}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Can we transcribe?
print("\nTest 4: Can we transcribe the audio?")
print("  This may take a minute...")

try:
    segments, info = model.transcribe(
        str(test_audio),
        beam_size=1,
        language="en",
        vad_filter=True,
    )
    print("✓ SUCCESS: Transcription started")
    print(f"  Language: {info.language}")
    print(f"  Duration: {info.duration:.1f}s")
    
    # Process a few segments
    print("\n  Processing segments...")
    count = 0
    for segment in segments:
        count += 1
        if count <= 3:
            print(f"    Segment {count}: {segment.text[:50]}...")
        if count >= 10:
            break
    
    print(f"\n✓ Processed {count} segments successfully")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    print(f"\nException type: {type(e).__name__}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print()
print("The transcription components are working correctly.")
print("If the GUI still crashes, the issue is likely:")
print("  1. Thread communication problem")
print("  2. Qt signal/slot issue")
print("  3. Exception not being caught properly")
print()
print("Next steps:")
print("  1. Check the log file: transcripts/transcriber_gui.log")
print("  2. Look for the last step completed before crash")
print("  3. Run the CLI version: python main_cli.py")
print()