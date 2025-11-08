#!/usr/bin/env python3
"""
PyQt5 Transcriber - SUBPROCESS VERSION
Uses CLI in subprocess to avoid all threading issues
Supports YouTube, Vimeo, 900+ sites, and local video/audio files
"""
import sys
import subprocess
import tempfile
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox, 
    QGroupBox, QMessageBox, QComboBox, QProgressBar, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QFont, QTextCursor

from logger import get_logger
from config import DEFAULT_URL, AVAILABLE_MODELS, OUTPUT_DIR
from downloader import download_audio, cleanup_audio
from file_operations import save_transcript
import json

# Initialize logger
log_file = OUTPUT_DIR / "transcriber_gui.log"
logger = get_logger(log_file)


class SubprocessTranscriberThread(QThread):
    """Worker that calls CLI via subprocess - NO threading issues!"""
    status_update = pyqtSignal(str, str)
    progress_update = pyqtSignal(int)
    finished_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, audio_file, title, model_size, include_timestamps):
        super().__init__()
        self.audio_file = audio_file
        self.title = title
        self.model_size = model_size
        self.include_timestamps = include_timestamps
    
    def emit_status(self, msg, msg_type="info"):
        if msg_type == "debug":
            logger.debug(msg)
        elif msg_type == "error":
            logger.error(msg)
        elif msg_type == "success":
            logger.success(msg)
        else:
            logger.info(msg)
        self.status_update.emit(msg, msg_type)
    
    def run(self):
        """Run transcription in subprocess"""
        logger.section("SUBPROCESS TRANSCRIPTION STARTED")
        
        try:
            # Create a Python script to run transcription
            script_code = f"""
import sys
sys.path.insert(0, r'{Path(__file__).parent}')

from transcriber import transcribe_audio

transcript = transcribe_audio(
    r'{self.audio_file}',
    '{self.model_size}',
    {self.include_timestamps}
)

if transcript:
    print("TRANSCRIPT_START")
    print(transcript)
    print("TRANSCRIPT_END")
    sys.exit(0)
else:
    print("ERROR: No transcript generated")
    sys.exit(1)
"""
            
            # Write temp script
            temp_script = OUTPUT_DIR / "temp_transcribe.py"
            temp_script.write_text(script_code, encoding='utf-8')
            
            self.emit_status("Running transcription in subprocess...", "info")
            self.progress_update.emit(40)
            
            # Run in subprocess
            logger.debug(f"Running: python {temp_script}")
            result = subprocess.run(
                [sys.executable, str(temp_script)],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            # Clean up temp script
            try:
                temp_script.unlink()
            except:
                pass
            
            self.progress_update.emit(90)
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Subprocess failed"
                logger.error(f"Subprocess error: {error_msg}")
                raise Exception(error_msg)
            
            # Parse output
            output = result.stdout
            
            if "TRANSCRIPT_START" in output and "TRANSCRIPT_END" in output:
                start = output.index("TRANSCRIPT_START") + len("TRANSCRIPT_START\n")
                end = output.index("TRANSCRIPT_END")
                transcript = output[start:end].strip()
                
                logger.success(f"Got transcript: {len(transcript)} chars")
                self.progress_update.emit(100)
                self.finished_signal.emit(transcript, self.title)
            else:
                raise Exception("Could not parse transcript from subprocess output")
                
        except subprocess.TimeoutExpired:
            logger.error("Subprocess timeout (10 minutes)")
            self.error_signal.emit("Transcription timeout - try a shorter video")
        except Exception as e:
            logger.error(f"Subprocess error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            self.error_signal.emit(str(e))


class YouTubeTranscriberGUI(QMainWindow):
    """GUI using subprocess approach"""
    
    def __init__(self):
        super().__init__()
        self.current_transcript = ""
        self.current_title = ""
        self.worker_thread = None
        self.audio_file = None
        self.is_local_file = False
        
        self.init_ui()
        self.apply_dark_theme()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Media Transcriber - Multi-Source")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Media Transcriber")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # URL/File Input with Browse button
        url_group = QGroupBox("Video URL or Local File")
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL (YouTube, Vimeo, etc.) or browse for local file...")
        self.url_input.setText(DEFAULT_URL)
        url_layout.addWidget(self.url_input)
        
        browse_button = QPushButton("📁 Browse")
        browse_button.clicked.connect(self.browse_file)
        browse_button.setMaximumWidth(120)
        url_layout.addWidget(browse_button)
        
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setCurrentText("tiny")
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        options_layout.addLayout(model_layout)
        
        self.save_audio_cb = QCheckBox("Save audio file")
        self.timestamps_cb = QCheckBox("Include timestamps")
        self.timestamps_cb.setChecked(True)
        options_layout.addWidget(self.save_audio_cb)
        options_layout.addWidget(self.timestamps_cb)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Start Transcription")
        self.start_button.clicked.connect(self.start_transcription)
        button_layout.addWidget(self.start_button)
        
        self.copy_button = QPushButton("📋 Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        self.save_button = QPushButton("💾 Save Transcript")
        self.save_button.clicked.connect(self.save_transcript_file)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        clear_button = QPushButton("🗑 Clear")
        clear_button.clicked.connect(self.clear_status)
        button_layout.addWidget(clear_button)
        
        main_layout.addLayout(button_layout)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Consolas", 10))
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
    
    def apply_dark_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 12pt;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 10px;
                font-size: 11pt;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 2px solid #888888;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #666666;
                border: 2px solid #3a3a3a;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 4px;
                font-size: 10pt;
                padding: 5px;
            }
            QComboBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 6px;
                font-size: 11pt;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #ffffff;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 11pt;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 2px solid #0078d4;
            }
            QGroupBox {
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 6px;
                margin-top: 12px;
                font-size: 12pt;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 4px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)
    
    def add_status(self, message, msg_type="info"):
        """Add status message"""
        colors = {
            "debug": "#888888",
            "info": "#ffffff",
            "success": "#4ec9b0",
            "error": "#f48771",
            "warning": "#dcdcaa"
        }
        color = colors.get(msg_type, "#ffffff")
        
        prefix = {
            "debug": "[DEBUG]",
            "error": "[ERROR]",
            "success": "[✓]",
            "warning": "[!]"
        }.get(msg_type, "")
        
        formatted = f'<span style="color:{color};">{prefix} {message}</span>'
        self.status_text.append(formatted)
        
        cursor = self.status_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.status_text.setTextCursor(cursor)
    
    def browse_file(self):
        """Browse for local video/audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video or Audio File",
            "",
            "Media Files (*.mp4 *.mp3 *.wav *.m4a *.webm *.mkv *.avi *.mov *.flac *.ogg);;All Files (*.*)"
        )
        
        if file_path:
            self.url_input.setText(file_path)
            self.add_status(f"Selected: {Path(file_path).name}", "info")
            logger.info(f"User selected local file: {file_path}")
    
    def start_transcription(self):
        """Start transcription"""
        logger.section("START BUTTON CLICKED")
        
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No Input", "Enter a URL or browse for a file!")
            return
        
        # Disable UI
        self.start_button.setEnabled(False)
        self.start_button.setText("⏳ Working...")
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        model = self.model_combo.currentText()
        save_audio = self.save_audio_cb.isChecked()
        timestamps = self.timestamps_cb.isChecked()
        
        self.add_status(f"Starting: {model} model", "info")
        
        # Check if it's a local file or URL
        try:
            # Check prerequisites
            from system_checks import check_ffmpeg, check_dependencies
            if not check_ffmpeg():
                raise Exception("FFmpeg not found")
            
            success, _ = check_dependencies()
            if not success:
                raise Exception("Missing dependencies")
            
            self.progress_bar.setValue(10)
            
            # Determine if local file or URL
            if Path(url).exists():
                # Local file
                self.is_local_file = True
                self.audio_file = Path(url)
                title = self.audio_file.stem
                self.add_status(f"Using local file: {self.audio_file.name}", "info")
                logger.info(f"Processing local file: {self.audio_file}")
                self.progress_bar.setValue(30)
                
            else:
                # URL (YouTube, Vimeo, etc.)
                self.is_local_file = False
                self.add_status("Downloading from URL...", "info")
                self.progress_bar.setValue(10)
                
                # yt-dlp supports 900+ sites automatically
                self.audio_file, title = download_audio(url, OUTPUT_DIR)
                self.add_status(f"✓ Downloaded: {self.audio_file.name}", "success")
                self.progress_bar.setValue(30)
            
            # Step 2: Transcribe in subprocess (works for both local and downloaded files)
            self.worker_thread = SubprocessTranscriberThread(
                self.audio_file, title, model, timestamps
            )
            self.worker_thread.status_update.connect(self.add_status)
            self.worker_thread.progress_update.connect(self.progress_bar.setValue)
            self.worker_thread.finished_signal.connect(
                lambda t, title: self.on_complete(t, title, save_audio)
            )
            self.worker_thread.error_signal.connect(
                lambda e: self.on_error(e, save_audio)
            )
            self.worker_thread.start()
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.on_error(str(e), False)
    
    def on_complete(self, transcript, title, save_audio):
        """Handle completion"""
        logger.success("Transcription complete!")
        
        self.current_transcript = transcript
        self.current_title = title
        
        self.add_status("="*60, "success")
        self.add_status(f"COMPLETE: {title}", "success")
        self.add_status("="*60, "success")
        
        lines = transcript.split('\n')[:10]
        for line in lines:
            self.status_text.append(line)
        
        if len(transcript.split('\n')) > 10:
            self.add_status(f"... ({len(transcript.split('\n'))} lines)", "info")
        
        # Cleanup audio if needed (only for downloaded files, not local files)
        if not save_audio and self.audio_file and not self.is_local_file:
            try:
                cleanup_audio(self.audio_file)
                self.add_status("Downloaded audio deleted", "info")
            except:
                pass
        
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(transcript)
        self.add_status("✓ Copied to clipboard!", "success")
        
        # Auto-save transcript to file
        try:
            output_file = save_transcript(transcript, title, OUTPUT_DIR)
            self.add_status(f"✓ Saved to: {output_file.name}", "success")
            logger.info(f"Auto-saved transcript to: {output_file}")
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            self.add_status("Warning: Could not auto-save file", "warning")
        
        # Re-enable UI
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Start Transcription")
        self.copy_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(self, "Done!", 
            f"Transcription complete!\n\n{len(transcript.split(chr(10)))} lines\n\nSaved to: {output_file.name}")
    
    def on_error(self, error, save_audio):
        """Handle error"""
        logger.error(f"Error: {error}")
        self.add_status(f"Failed: {error}", "error")
        
        # Cleanup audio if needed (only for downloaded files)
        if not save_audio and self.audio_file and not self.is_local_file:
            try:
                cleanup_audio(self.audio_file)
            except:
                pass
        
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Start Transcription")
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error", f"Failed:\n\n{error}")
    
    def copy_to_clipboard(self):
        """Copy to clipboard"""
        if self.current_transcript:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_transcript)
            self.add_status("Copied!", "success")
            QMessageBox.information(self, "Copied", "Transcript copied!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No transcript!")
    
    def save_transcript_file(self):
        """Save transcript (manual save button)"""
        if not self.current_transcript:
            QMessageBox.warning(self, "Nothing to Save", "No transcript!")
            return
        
        try:
            output_file = save_transcript(self.current_transcript, self.current_title, OUTPUT_DIR)
            self.add_status(f"Saved: {output_file}", "success")
            QMessageBox.information(self, "Saved", f"Saved to:\n{output_file}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")
    
    def clear_status(self):
        """Clear status"""
        self.status_text.clear()
        self.add_status("Ready.", "info")


def main():
    """Main entry point"""
    logger.section("MULTI-SOURCE GUI STARTING")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Media Transcriber")
    
    window = YouTubeTranscriberGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)