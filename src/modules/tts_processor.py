"""Text-to-Speech (TTS) module using Coqui TTS (XTTS-v2)"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import torch
import numpy as np
from TTS.api import TTS
import soundfile as sf

from config import TTS_CONFIG, MODELS_DIR, DOWNLOADS_DIR

logger = logging.getLogger(__name__)


class TTSProcessor:
    """Handles text-to-speech synthesis using Coqui TTS (XTTS-v2)"""
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None,
                 speaker_wav: Optional[str] = None):
        """
        Initialize TTS processor
        
        Args:
            model_name: Name of the TTS model
            device: Device to use (auto, cpu, cuda)
            speaker_wav: Path to reference audio for voice cloning
        """
        self.model_name = model_name or TTS_CONFIG["model_name"]
        self.device = device or TTS_CONFIG["device"]
        self.speaker_wav = speaker_wav or TTS_CONFIG["speaker_wav"]
        self.language = TTS_CONFIG["language"]
        self.tts = None
        
        # Auto-detect device if set to auto
        if self.device == "auto":
            self.device = self._detect_device()
            
        logger.info(f"Initializing TTS with model: {self.model_name}, device: {self.device}")
        
    def _detect_device(self) -> str:
        """Detect available device (CUDA or CPU)"""
        if torch.cuda.is_available():
            logger.info("CUDA available, using GPU for TTS")
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("MPS available, but using CPU for TTS (better compatibility)")
            return "cpu"
        else:
            logger.info("No GPU available, using CPU for TTS")
            return "cpu"
            
    def load_model(self):
        """Load the TTS model"""
        if self.tts is not None:
            logger.info("TTS model already loaded")
            return
            
        try:
            logger.info(f"Loading TTS model: {self.model_name}")
            
            # Initialize TTS
            self.tts = TTS(
                model_name=self.model_name,
                progress_bar=False,
                gpu=(self.device == "cuda")
            )
            
            logger.info("TTS model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading TTS model: {e}")
            raise
            
    def set_speaker_reference(self, speaker_wav: str):
        """
        Set reference audio for voice cloning
        
        Args:
            speaker_wav: Path to reference audio file
        """
        if not os.path.exists(speaker_wav):
            raise FileNotFoundError(f"Speaker reference audio not found: {speaker_wav}")
            
        self.speaker_wav = speaker_wav
        logger.info(f"Speaker reference set to: {speaker_wav}")
        
    def synthesize_text(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            output_path: Path to save output audio (optional)
            
        Returns:
            Path to generated audio file
        """
        if self.tts is None:
            self.load_model()
            
        if not text or not text.strip():
            logger.warning("Empty text provided, skipping synthesis")
            return None
            
        if output_path is None:
            output_path = DOWNLOADS_DIR / "tts_output.wav"
        else:
            output_path = Path(output_path)
            
        try:
            logger.info(f"Synthesizing text: {text[:50]}...")
            
            # If we have a speaker reference, use voice cloning
            if self.speaker_wav and os.path.exists(self.speaker_wav):
                logger.info(f"Using voice cloning with reference: {self.speaker_wav}")
                
                self.tts.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    speaker_wav=self.speaker_wav,
                    language=self.language,
                    temperature=TTS_CONFIG.get("temperature", 0.7),
                )
            else:
                logger.warning("No speaker reference provided, using default voice")
                
                self.tts.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    language=self.language,
                )
            
            logger.info(f"Audio synthesized and saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error synthesizing text: {e}")
            raise
            
    def synthesize_segments(self, segments: List[Dict], output_dir: Optional[str] = None) -> List[Dict]:
        """
        Synthesize speech for multiple segments
        
        Args:
            segments: List of segments with translated text
            output_dir: Directory to save segment audio files
            
        Returns:
            List of segments with audio file paths
        """
        if self.tts is None:
            self.load_model()
            
        if output_dir is None:
            output_dir = DOWNLOADS_DIR / "segments"
        else:
            output_dir = Path(output_dir)
            
        output_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Synthesizing {len(segments)} segments")
        
        synthesized_segments = []
        
        for i, segment in enumerate(segments):
            try:
                text = segment.get("translated_text", segment.get("text", ""))
                
                if not text or not text.strip():
                    logger.warning(f"Segment {i} has no text, skipping")
                    synthesized_segments.append({
                        **segment,
                        "audio_path": None
                    })
                    continue
                
                # Generate output path for this segment
                segment_output = output_dir / f"segment_{i:04d}.wav"
                
                # Synthesize
                audio_path = self.synthesize_text(text, segment_output)
                
                # Add audio path to segment
                synthesized_segment = {
                    **segment,
                    "audio_path": audio_path
                }
                
                synthesized_segments.append(synthesized_segment)
                
                logger.info(f"Segment {i+1}/{len(segments)} synthesized: {text[:30]}...")
                
            except Exception as e:
                logger.error(f"Error synthesizing segment {i}: {e}")
                synthesized_segments.append({
                    **segment,
                    "audio_path": None
                })
        
        logger.info(f"Synthesis completed for {len(synthesized_segments)} segments")
        return synthesized_segments
        
    def combine_segments(self, segments: List[Dict], output_path: str, 
                        sample_rate: int = 16000) -> str:
        """
        Combine segment audio files with proper timing
        
        Args:
            segments: List of segments with audio paths and timing
            output_path: Path to save combined audio
            sample_rate: Sample rate for output audio
            
        Returns:
            Path to combined audio file
        """
        logger.info(f"Combining {len(segments)} audio segments")
        
        try:
            # Calculate total duration
            if segments:
                total_duration = segments[-1]["end"]
            else:
                logger.error("No segments to combine")
                return None
                
            # Create silent audio of total duration
            total_samples = int(total_duration * sample_rate)
            combined_audio = np.zeros(total_samples, dtype=np.float32)
            
            # Add each segment at its proper position
            for i, segment in enumerate(segments):
                audio_path = segment.get("audio_path")
                
                if not audio_path or not os.path.exists(audio_path):
                    logger.warning(f"Segment {i} audio not found, skipping")
                    continue
                
                # Load segment audio
                audio, sr = sf.read(audio_path)
                
                # Resample if needed
                if sr != sample_rate:
                    import librosa
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
                
                # Calculate position in combined audio
                start_sample = int(segment["start"] * sample_rate)
                end_sample = start_sample + len(audio)
                
                # Ensure we don't exceed array bounds
                if end_sample > len(combined_audio):
                    end_sample = len(combined_audio)
                    audio = audio[:end_sample - start_sample]
                
                # Add to combined audio
                combined_audio[start_sample:end_sample] = audio
                
            # Save combined audio
            sf.write(output_path, combined_audio, sample_rate)
            
            logger.info(f"Combined audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining segments: {e}")
            raise
            
    def unload_model(self):
        """Unload model to free memory"""
        if self.tts is not None:
            logger.info("Unloading TTS model")
            del self.tts
            self.tts = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
