"""Audio processing module for extracting, converting, and manipulating audio files"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import ffmpeg
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

from config import AUDIO_CONFIG, VIDEO_CONFIG, DOWNLOADS_DIR

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handles audio extraction, conversion, and processing"""
    
    def __init__(self):
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.channels = AUDIO_CONFIG["channels"]
        self.bit_depth = AUDIO_CONFIG["bit_depth"]
        
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file using ffmpeg
        
        Args:
            video_path: Path to input video file
            output_path: Path for output audio file (optional)
            
        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)
        
        if output_path is None:
            output_path = DOWNLOADS_DIR / f"{video_path.stem}_audio.wav"
        else:
            output_path = Path(output_path)
            
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec='pcm_s16le',
                ac=self.channels,
                ar=self.sample_rate,
                loglevel='error'
            )
            ffmpeg.run(stream, overwrite_output=True)
            
            logger.info(f"Audio extracted to {output_path}")
            return str(output_path)
            
        except ffmpeg.Error as e:
            logger.error(f"Error extracting audio: {e}")
            raise
            
    def convert_to_wav(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert audio file to WAV format with specified parameters
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for output WAV file (optional)
            
        Returns:
            Path to converted WAV file
        """
        audio_path = Path(audio_path)
        
        if output_path is None:
            output_path = DOWNLOADS_DIR / f"{audio_path.stem}_converted.wav"
        else:
            output_path = Path(output_path)
            
        logger.info(f"Converting {audio_path} to WAV format")
        
        try:
            # Load audio file
            audio, sr = librosa.load(str(audio_path), sr=self.sample_rate, mono=(self.channels == 1))
            
            # Normalize if configured
            if AUDIO_CONFIG.get("normalize", True):
                audio = librosa.util.normalize(audio)
            
            # Save as WAV
            sf.write(str(output_path), audio, self.sample_rate)
            
            logger.info(f"Audio converted to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise
            
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and return audio data and sample rate
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        logger.info(f"Loading audio from {audio_path}")
        
        try:
            audio, sr = librosa.load(str(audio_path), sr=self.sample_rate, mono=(self.channels == 1))
            return audio, sr
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            raise
            
    def save_audio(self, audio_data: np.ndarray, output_path: str, sample_rate: Optional[int] = None) -> str:
        """
        Save audio data to file
        
        Args:
            audio_data: Audio data as numpy array
            output_path: Path for output file
            sample_rate: Sample rate (uses config default if not specified)
            
        Returns:
            Path to saved audio file
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
            
        logger.info(f"Saving audio to {output_path}")
        
        try:
            sf.write(output_path, audio_data, sample_rate)
            logger.info(f"Audio saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            raise
            
    def replace_audio_in_video(self, video_path: str, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Replace audio track in video file
        
        Args:
            video_path: Path to input video file
            audio_path: Path to new audio file
            output_path: Path for output video file (optional)
            
        Returns:
            Path to output video file
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        
        if output_path is None:
            output_path = DOWNLOADS_DIR / f"{video_path.stem}_translated.mp4"
        else:
            output_path = Path(output_path)
            
        logger.info(f"Replacing audio in video: {video_path}")
        
        try:
            video_stream = ffmpeg.input(str(video_path))
            audio_stream = ffmpeg.input(str(audio_path))
            
            stream = ffmpeg.output(
                video_stream.video,
                audio_stream.audio,
                str(output_path),
                vcodec='copy',
                acodec=VIDEO_CONFIG.get("audio_codec", "aac"),
                audio_bitrate=VIDEO_CONFIG.get("audio_bitrate", "192k"),
                loglevel='error'
            )
            
            ffmpeg.run(stream, overwrite_output=True)
            
            logger.info(f"Video with new audio saved to {output_path}")
            return str(output_path)
            
        except ffmpeg.Error as e:
            logger.error(f"Error replacing audio in video: {e}")
            raise
            
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get duration of audio file in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            raise
            
    def time_stretch(self, audio_data: np.ndarray, rate: float) -> np.ndarray:
        """
        Time-stretch audio without changing pitch
        
        Args:
            audio_data: Audio data as numpy array
            rate: Stretch factor (> 1.0 speeds up, < 1.0 slows down)
            
        Returns:
            Time-stretched audio data
        """
        try:
            stretched = librosa.effects.time_stretch(audio_data, rate=rate)
            return stretched
        except Exception as e:
            logger.error(f"Error time-stretching audio: {e}")
            raise
            
    def match_duration(self, audio_data: np.ndarray, target_duration: float, sample_rate: int) -> np.ndarray:
        """
        Adjust audio to match target duration
        
        Args:
            audio_data: Audio data as numpy array
            target_duration: Target duration in seconds
            sample_rate: Sample rate of audio
            
        Returns:
            Duration-matched audio data
        """
        current_duration = len(audio_data) / sample_rate
        rate = current_duration / target_duration
        
        logger.info(f"Matching duration: {current_duration:.2f}s -> {target_duration:.2f}s (rate: {rate:.2f})")
        
        return self.time_stretch(audio_data, rate)
