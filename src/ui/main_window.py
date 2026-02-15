"""Main GUI module using PyQt6"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QFileDialog, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from config import UI_CONFIG, SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_FORMATS, OUTPUT_DIR


class ProcessingThread(QThread):
    """Thread for processing audio/video files without blocking UI"""
    
    progress_update = pyqtSignal(int, str)  # progress percentage, message
    finished = pyqtSignal(bool, str)  # success, message/error
    
    def __init__(self, input_file, mode, sync_duration, use_gpu, speaker_ref=None):
        super().__init__()
        self.input_file = input_file
        self.mode = mode
        self.sync_duration = sync_duration
        self.use_gpu = use_gpu
        self.speaker_ref = speaker_ref
        
    def run(self):
        """Run the processing pipeline"""
        try:
            # Import processors here to avoid loading at startup
            from src.modules.audio_processor import AudioProcessor
            from src.modules.asr_processor import ASRProcessor
            from src.modules.translation_processor import TranslationProcessor
            from src.modules.tts_processor import TTSProcessor
            
            self.progress_update.emit(5, "Initializing processors...")
            
            # Initialize processors
            audio_proc = AudioProcessor()
            
            # Detect if input is video or audio
            input_path = Path(self.input_file)
            is_video = input_path.suffix.lower() in SUPPORTED_VIDEO_FORMATS
            
            # Step 1: Extract/Convert Audio
            self.progress_update.emit(10, "Extracting audio...")
            
            if is_video:
                audio_path = audio_proc.extract_audio_from_video(self.input_file)
            else:
                audio_path = audio_proc.convert_to_wav(self.input_file)
            
            # Step 2: ASR (Speech Recognition)
            self.progress_update.emit(20, "Recognizing speech (this may take a while)...")
            
            # Set model size based on mode
            asr_model = "large-v3" if self.mode == "Контекстный (максимальное качество)" else "medium"
            device = "auto" if self.use_gpu else "cpu"
            
            asr_proc = ASRProcessor(model_size=asr_model, device=device)
            transcription = asr_proc.transcribe(audio_path)
            
            self.progress_update.emit(40, f"Speech recognized: {len(transcription['segments'])} segments")
            
            # Save transcription
            trans_file = OUTPUT_DIR / f"{input_path.stem}_transcription.txt"
            asr_proc.save_transcription(transcription, str(trans_file))
            
            # Save subtitles
            srt_file = OUTPUT_DIR / f"{input_path.stem}_russian.srt"
            asr_proc.save_subtitles(transcription, str(srt_file))
            
            # Step 3: Translation
            self.progress_update.emit(50, "Translating text...")
            
            trans_proc = TranslationProcessor(device=device)
            
            if self.mode == "Контекстный (максимальное качество)":
                translated_segments = trans_proc.translate_with_context(transcription["segments"])
            else:
                translated_segments = trans_proc.translate_segments(transcription["segments"])
            
            self.progress_update.emit(65, "Translation completed")
            
            # Save translation
            translation_file = OUTPUT_DIR / f"{input_path.stem}_translation.txt"
            trans_proc.save_translation(translated_segments, str(translation_file))
            
            # Step 4: TTS (Text-to-Speech)
            self.progress_update.emit(70, "Synthesizing speech...")
            
            tts_proc = TTSProcessor(device=device, speaker_wav=self.speaker_ref)
            synthesized_segments = tts_proc.synthesize_segments(translated_segments)
            
            self.progress_update.emit(85, "Combining audio segments...")
            
            # Combine segments
            combined_audio = OUTPUT_DIR / f"{input_path.stem}_translated_audio.wav"
            tts_proc.combine_segments(synthesized_segments, str(combined_audio))
            
            # Step 5: Duration matching if requested
            if self.sync_duration:
                self.progress_update.emit(90, "Synchronizing duration with original...")
                
                original_duration = audio_proc.get_audio_duration(audio_path)
                translated_duration = audio_proc.get_audio_duration(str(combined_audio))
                
                if abs(original_duration - translated_duration) > 1.0:  # More than 1 second difference
                    audio_data, sr = audio_proc.load_audio(str(combined_audio))
                    matched_audio = audio_proc.match_duration(audio_data, original_duration, sr)
                    audio_proc.save_audio(matched_audio, str(combined_audio), sr)
            
            # Step 6: Final export
            self.progress_update.emit(95, "Exporting final result...")
            
            if is_video:
                # Replace audio in video
                final_output = OUTPUT_DIR / f"{input_path.stem}_translated.mp4"
                audio_proc.replace_audio_in_video(self.input_file, str(combined_audio), str(final_output))
            else:
                # Just save the audio
                final_output = OUTPUT_DIR / f"{input_path.stem}_translated.wav"
                import shutil
                shutil.copy(str(combined_audio), str(final_output))
            
            self.progress_update.emit(100, "Processing completed!")
            
            # Clean up
            asr_proc.unload_model()
            trans_proc.unload_model()
            tts_proc.unload_model()
            
            self.finished.emit(True, f"Success! Output saved to:\n{final_output}")
            
        except Exception as e:
            self.finished.emit(False, f"Error during processing:\n{str(e)}")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.input_file = None
        self.speaker_ref = None
        self.processing_thread = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(UI_CONFIG["window_title"])
        self.setGeometry(100, 100, UI_CONFIG["window_width"], UI_CONFIG["window_height"])
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Offline Voice-to-Voice Translator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # File input section
        file_group = QGroupBox("Input File")
        file_layout = QVBoxLayout()
        
        file_input_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("padding: 5px; border: 1px solid #ccc;")
        file_input_layout.addWidget(self.file_path_label)
        
        self.load_button = QPushButton("Load File")
        self.load_button.clicked.connect(self.load_file)
        file_input_layout.addWidget(self.load_button)
        
        file_layout.addLayout(file_input_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Speaker reference section
        speaker_group = QGroupBox("Voice Reference (Optional)")
        speaker_layout = QVBoxLayout()
        
        speaker_input_layout = QHBoxLayout()
        self.speaker_path_label = QLabel("No reference audio selected (will use default voice)")
        self.speaker_path_label.setStyleSheet("padding: 5px; border: 1px solid #ccc;")
        speaker_input_layout.addWidget(self.speaker_path_label)
        
        self.load_speaker_button = QPushButton("Load Reference")
        self.load_speaker_button.clicked.connect(self.load_speaker_reference)
        speaker_input_layout.addWidget(self.load_speaker_button)
        
        speaker_layout.addLayout(speaker_input_layout)
        speaker_group.setLayout(speaker_layout)
        main_layout.addWidget(speaker_group)
        
        # Settings section
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Translation Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Быстрый", "Контекстный (максимальное качество)"])
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)
        
        # Checkboxes
        self.sync_duration_check = QCheckBox("Синхронизировать длительность с оригиналом")
        self.sync_duration_check.setChecked(True)
        settings_layout.addWidget(self.sync_duration_check)
        
        self.use_gpu_check = QCheckBox("Использовать GPU (если доступен)")
        self.use_gpu_check.setChecked(True)
        settings_layout.addWidget(self.use_gpu_check)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Process button
        self.process_button = QPushButton("Обработать")
        self.process_button.setStyleSheet("padding: 10px; font-size: 14px; font-weight: bold;")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setEnabled(False)
        main_layout.addWidget(self.process_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Log window
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Export button
        self.export_button = QPushButton("Открыть папку с результатами")
        self.export_button.clicked.connect(self.open_output_folder)
        main_layout.addWidget(self.export_button)
        
        self.log("Application initialized. Ready to process files.")
        
    def load_file(self):
        """Load input audio or video file"""
        file_filter = "Media Files (*.mp4 *.mov *.mkv *.avi *.webm *.wav *.mp3 *.flac *.ogg *.m4a);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", file_filter)
        
        if file_path:
            self.input_file = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.process_button.setEnabled(True)
            self.log(f"Loaded file: {file_path}")
            
    def load_speaker_reference(self):
        """Load speaker reference audio for voice cloning"""
        file_filter = "Audio Files (*.wav *.mp3 *.flac);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Reference Audio", "", file_filter)
        
        if file_path:
            self.speaker_ref = file_path
            self.speaker_path_label.setText(os.path.basename(file_path))
            self.log(f"Loaded speaker reference: {file_path}")
            
    def start_processing(self):
        """Start processing the file"""
        if not self.input_file:
            QMessageBox.warning(self, "No File", "Please load a file first.")
            return
        
        # Disable controls during processing
        self.process_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.load_speaker_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log("Starting processing...")
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(
            self.input_file,
            self.mode_combo.currentText(),
            self.sync_duration_check.isChecked(),
            self.use_gpu_check.isChecked(),
            self.speaker_ref
        )
        
        self.processing_thread.progress_update.connect(self.update_progress)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.start()
        
    def update_progress(self, value, message):
        """Update progress bar and log"""
        self.progress_bar.setValue(value)
        self.log(message)
        
    def processing_finished(self, success, message):
        """Handle processing completion"""
        # Re-enable controls
        self.process_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.load_speaker_button.setEnabled(True)
        
        if success:
            self.log("✓ " + message)
            QMessageBox.information(self, "Success", message)
        else:
            self.log("✗ " + message)
            QMessageBox.critical(self, "Error", message)
            
    def open_output_folder(self):
        """Open the output folder"""
        import subprocess
        import platform
        
        output_path = str(OUTPUT_DIR)
        
        if platform.system() == "Windows":
            os.startfile(output_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", output_path])
        else:  # Linux
            subprocess.run(["xdg-open", output_path])
            
        self.log(f"Opened output folder: {output_path}")
        
    def log(self, message):
        """Add message to log window"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Main entry point for the GUI application"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
