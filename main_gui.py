#!/usr/bin/env python3
"""
PyQt5 Transcriber & Downloader
"""
import sys
import subprocess
import tempfile
import os
from pathlib import Path

# Fix for DLL issues
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox, 
    QGroupBox, QMessageBox, QComboBox, QProgressBar, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

from logger import get_logger
from config import DEFAULT_URL, AVAILABLE_MODELS, OUTPUT_DIR
from downloader import download_media, cleanup_audio
from file_operations import save_transcript

log_file = OUTPUT_DIR / "transcriber_gui.log"
logger = get_logger(log_file)


class FullProcessThread(QThread):
    """Handles download and optional transcription"""
    status_update = pyqtSignal(str, str)
    progress_update = pyqtSignal(int)
    finished_signal = pyqtSignal(str, str, str)  # transcript, title, final_file_path
    error_signal = pyqtSignal(str)
    
    def __init__(self, url, model_size, timestamps, save_media, media_type, skip_transcription):
        super().__init__()
        self.url = url
        self.model_size = model_size
        self.timestamps = timestamps
        self.save_media = save_media
        self.media_type = media_type
        self.skip_transcription = skip_transcription
        self.media_file = None
        self.title = "Unknown"
        self.is_local = False
    
    def emit_status(self, msg, msg_type="info"):
        self.status_update.emit(msg, msg_type)
        if msg_type == "error": logger.error(msg)
        elif msg_type == "success": logger.success(msg)
        else: logger.info(msg)

    def run(self):
        try:
            # Step 1: Download or locate
            if Path(self.url).exists():
                self.is_local = True
                self.media_file = Path(self.url)
                self.title = self.media_file.stem
                self.emit_status(f"Using local file: {self.media_file.name}")
            else:
                self.is_local = False
                self.emit_status(f"Downloading {self.media_type} from URL...")
                self.progress_update.emit(10)
                self.media_file, self.title = download_media(self.url, OUTPUT_DIR, type=self.media_type)
                self.emit_status(f"Download complete: {self.media_file.name}", "success")
            
            self.progress_update.emit(40)
            
            if self.skip_transcription:
                self.progress_update.emit(100)
                self.finished_signal.emit("", self.title, str(self.media_file))
                return

            # Step 2: Transcribe
            self.emit_status("Starting transcription...")
            script_code = f"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import sys
from pathlib import Path
sys.path.insert(0, r'{Path(__file__).parent}')
from transcriber import transcribe_audio
try:
    transcript = transcribe_audio(r'{self.media_file}', '{self.model_size}', {self.timestamps})
    if transcript:
        print("TRANSCRIPT_START")
        print(transcript)
        print("TRANSCRIPT_END")
        sys.exit(0)
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
            temp_script = OUTPUT_DIR / f"temp_task_{os.getpid()}.py"
            temp_script.write_text(script_code, encoding='utf-8')
            
            self.progress_update.emit(50)
            result = subprocess.run([sys.executable, str(temp_script)], capture_output=True, text=True, timeout=3600)
            try: temp_script.unlink()
            except: pass
            
            if result.returncode == 0 and "TRANSCRIPT_START" in result.stdout:
                output = result.stdout
                start = output.index("TRANSCRIPT_START") + len("TRANSCRIPT_START\n")
                end = output.index("TRANSCRIPT_END")
                transcript = output[start:end].strip()
                self.progress_update.emit(100)
                self.finished_signal.emit(transcript, self.title, str(self.media_file))
            else:
                raise Exception(f"Transcription failed: {result.stderr}")

        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            if not self.save_media and self.media_file and not self.is_local:
                cleanup_audio(self.media_file)


class YouTubeTranscriberGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_transcript = ""
        self.current_title = ""
        self.init_ui()
        self.apply_dark_theme()
    
    def init_ui(self):
        self.setWindowTitle("Media Downloader & Transcriber")
        self.setGeometry(100, 100, 900, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        title = QLabel("Media Downloader & Transcriber")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Input
        url_group = QGroupBox("Target URL or Local File")
        url_lay = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setText(DEFAULT_URL)
        url_lay.addWidget(self.url_input)
        btn_browse = QPushButton("📁 Browse")
        btn_browse.clicked.connect(self.browse)
        url_lay.addWidget(btn_browse)
        url_group.setLayout(url_lay)
        layout.addWidget(url_group)
        
        # Options
        opt_group = QGroupBox("Settings")
        opt_lay = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Download Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["audio", "video"])
        row1.addWidget(self.type_combo)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Whisper Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        row1.addWidget(self.model_combo)
        row1.addStretch()
        opt_lay.addLayout(row1)
        
        self.cb_skip = QCheckBox("Skip Transcription (Download Only)")
        self.cb_save = QCheckBox("Keep Media File (Don't delete after transcription)")
        self.cb_save.setChecked(True)
        self.cb_ts = QCheckBox("Include Timestamps in transcript")
        self.cb_ts.setChecked(True)
        
        opt_lay.addWidget(self.cb_skip)
        opt_lay.addWidget(self.cb_save)
        opt_lay.addWidget(self.cb_ts)
        opt_group.setLayout(opt_lay)
        layout.addWidget(opt_group)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        btns = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Run Task")
        self.btn_start.clicked.connect(self.run_task)
        btns.addWidget(self.btn_start)
        
        self.btn_copy = QPushButton("📋 Copy Transcript")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(self.current_transcript))
        btns.addWidget(self.btn_copy)
        
        layout.addLayout(btns)
        
        self.status = QTextEdit()
        self.status.setReadOnly(True)
        layout.addWidget(self.status)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
            QLabel { color: #ffffff; font-size: 11pt; }
            QLineEdit, QTextEdit { background-color: #1e1e1e; color: #ffffff; border: 1px solid #555; padding: 5px; }
            QPushButton { background-color: #3a3a3a; border: 1px solid #555; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #4a4a4a; }
            QComboBox { background-color: #3a3a3a; color: white; border: 1px solid #555; }
            QProgressBar { border: 1px solid #555; text-align: center; }
            QProgressBar::chunk { background-color: #0078d4; }
        """)

    def add_status(self, msg, mtype="info"):
        col = {"info": "#fff", "success": "#4ec9b0", "error": "#f48771"}.get(mtype, "#fff")
        self.status.append(f'<span style="color:{col};">{msg}</span>')
        self.status.moveCursor(QTextCursor.End)

    def browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open Media")
        if p: self.url_input.setText(p)

    def run_task(self):
        url = self.url_input.text().strip()
        if not url: return

        self.btn_start.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status.clear()
        self.add_status(f"Starting task...")

        try:
            from system_checks import check_ffmpeg, check_dependencies
            if not check_ffmpeg(): raise Exception("FFmpeg not found")
            if not check_dependencies(skip_torch=self.cb_skip.isChecked()): raise Exception("Dependencies failed")

            self.thread = FullProcessThread(
                url, self.model_combo.currentText(), self.cb_ts.isChecked(), 
                self.cb_save.isChecked(), self.type_combo.currentText(), self.cb_skip.isChecked()
            )
            self.thread.status_update.connect(self.add_status)
            self.thread.progress_update.connect(self.progress.setValue)
            self.thread.finished_signal.connect(self.on_done)
            self.thread.error_signal.connect(self.on_fail)
            self.thread.start()
        except Exception as e:
            self.on_fail(str(e))

    def on_done(self, transcript, title, file_path):
        self.current_transcript = transcript
        self.current_title = title
        self.progress.setVisible(False)
        self.btn_start.setEnabled(True)
        
        if transcript:
            self.add_status(f"✓ Transcription complete for {title}", "success")
            self.btn_copy.setEnabled(True)
            save_transcript(transcript, title, OUTPUT_DIR)
        else:
            self.add_status(f"✓ Download complete: {Path(file_path).name}", "success")
            
        QMessageBox.information(self, "Success", f"Task finished successfully!\n\nFile: {Path(file_path).name}")

    def on_fail(self, err):
        self.add_status(f"✗ Error: {err}", "error")
        self.progress.setVisible(False)
        self.btn_start.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed: {err}")

def main():
    app = QApplication(sys.argv)
    window = YouTubeTranscriberGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
