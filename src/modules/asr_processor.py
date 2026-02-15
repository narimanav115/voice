"""Automatic Speech Recognition (ASR) module using Faster Whisper"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import torch
from faster_whisper import WhisperModel

from config import ASR_CONFIG, MODELS_DIR

logger = logging.getLogger(__name__)


class ASRProcessor:
    """Handles automatic speech recognition using Faster Whisper"""
    
    def __init__(self, model_size: Optional[str] = None, device: Optional[str] = None, 
                 compute_type: Optional[str] = None):
        """
        Initialize ASR processor
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to use (auto, cpu, cuda)
            compute_type: Compute type (float16, int8, float32)
        """
        self.model_size = model_size or ASR_CONFIG["model_name"]
        self.device = device or ASR_CONFIG["device"]
        self.compute_type = compute_type or ASR_CONFIG["compute_type"]
        self.language = ASR_CONFIG["language"]
        self.model = None
        
        # Auto-detect device if set to auto
        if self.device == "auto":
            self.device = self._detect_device()
            
        logger.info(f"Initializing ASR with model: {self.model_size}, device: {self.device}, compute_type: {self.compute_type}")
        
    def _detect_device(self) -> str:
        """Detect available device (CUDA, MPS, or CPU)"""
        if torch.cuda.is_available():
            logger.info("CUDA available, using GPU")
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("MPS (Metal) available, using GPU")
            # Note: faster-whisper might not fully support MPS, fallback to CPU
            return "cpu"
        else:
            logger.info("No GPU available, using CPU")
            return "cpu"
            
    def load_model(self):
        """Load the Whisper model"""
        if self.model is not None:
            logger.info("Model already loaded")
            return
            
        try:
            logger.info(f"Loading Whisper model: {self.model_size}")
            
            # Adjust compute type based on device
            compute_type = self.compute_type
            if self.device == "cpu":
                if compute_type == "float16":
                    compute_type = "float32"
                    logger.info("Changed compute_type to float32 for CPU")
            
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type,
                download_root=str(MODELS_DIR / "whisper")
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
            
    def transcribe(self, audio_path: str, return_segments: bool = True) -> Dict:
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file
            return_segments: Whether to return detailed segments
            
        Returns:
            Dictionary containing transcription results
        """
        if self.model is None:
            self.load_model()
            
        logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=ASR_CONFIG["beam_size"],
                vad_filter=ASR_CONFIG["vad_filter"],
                vad_parameters=ASR_CONFIG.get("vad_parameters"),
            )
            
            # Convert segments to list
            segments_list = []
            full_text = []
            
            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "duration": segment.end - segment.start,
                    "text": segment.text.strip(),
                    "words": []
                }
                
                # Add word-level timestamps if available
                if hasattr(segment, 'words') and segment.words:
                    segment_dict["words"] = [
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                        }
                        for word in segment.words
                    ]
                
                segments_list.append(segment_dict)
                full_text.append(segment.text.strip())
            
            result = {
                "text": " ".join(full_text),
                "segments": segments_list if return_segments else [],
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
            }
            
            logger.info(f"Transcription completed. Language: {info.language}, Duration: {info.duration:.2f}s")
            logger.info(f"Detected {len(segments_list)} segments")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
            
    def save_transcription(self, transcription: Dict, output_path: str):
        """
        Save transcription to text file
        
        Args:
            transcription: Transcription dictionary
            output_path: Path to output file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcription["text"])
            logger.info(f"Transcription saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
            raise
            
    def save_subtitles(self, transcription: Dict, output_path: str):
        """
        Save transcription as SRT subtitles
        
        Args:
            transcription: Transcription dictionary
            output_path: Path to output SRT file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(transcription["segments"], start=1):
                    start_time = self._format_timestamp(segment["start"])
                    end_time = self._format_timestamp(segment["end"])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text']}\n")
                    f.write("\n")
                    
            logger.info(f"Subtitles saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving subtitles: {e}")
            raise
            
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            logger.info("Unloading ASR model")
            del self.model
            self.model = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
