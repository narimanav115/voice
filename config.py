"""Configuration file for Voice Changer application"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.absolute()
MODELS_DIR = BASE_DIR / "models"
DOWNLOADS_DIR = BASE_DIR / "downloads"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [MODELS_DIR, DOWNLOADS_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# ASR Configuration
ASR_CONFIG = {
    "model_name": "large-v3",  # Options: tiny, base, small, medium, large-v2, large-v3
    "device": "auto",  # auto, cpu, cuda
    "compute_type": "float16",  # float16, int8, float32
    "language": "ru",
    "beam_size": 5,
    "vad_filter": True,
    "vad_parameters": {
        "threshold": 0.5,
        "min_speech_duration_ms": 250,
        "max_speech_duration_s": 30,
        "min_silence_duration_ms": 2000,
        "speech_pad_ms": 400,
    }
}

# Translation Configuration
TRANSLATION_CONFIG = {
    "model_name": "facebook/nllb-200-distilled-1.3B",  # or facebook/nllb-200-distilled-600M
    "source_lang": "rus_Cyrl",
    "target_lang": "eng_Latn",
    "device": "auto",
    "max_length": 512,
    "num_beams": 4,
}

# TTS Configuration
TTS_CONFIG = {
    "model_name": "tts_models/multilingual/multi-dataset/xtts_v2",
    "language": "en",
    "device": "auto",
    "speaker_wav": None,  # Path to reference audio for voice cloning
    "temperature": 0.7,
    "length_penalty": 1.0,
    "repetition_penalty": 2.0,
    "top_k": 50,
    "top_p": 0.85,
}

# Voice Conversion Configuration (RVC)
RVC_CONFIG = {
    "model_path": None,  # Path to trained RVC model
    "f0_up_key": 0,  # Pitch adjustment
    "f0_method": "crepe",  # crepe, harvest, dio
    "index_rate": 0.75,
    "protect": 0.33,
    "filter_radius": 3,
}

# Audio Processing Configuration
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,  # mono
    "bit_depth": 16,
    "format": "wav",
    "normalize": True,
}

# Video Processing Configuration
VIDEO_CONFIG = {
    "extract_audio": True,
    "replace_audio_track": True,
    "output_format": "mp4",
    "video_codec": "libx264",
    "audio_codec": "aac",
    "audio_bitrate": "192k",
}

# Supported file formats
SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".mkv", ".avi", ".webm"]

# Processing modes
PROCESSING_MODES = {
    "fast": {
        "asr_model": "medium",
        "translation_model": "facebook/nllb-200-distilled-600M",
        "compute_type": "int8",
    },
    "quality": {
        "asr_model": "large-v3",
        "translation_model": "facebook/nllb-200-distilled-1.3B",
        "compute_type": "float16",
    }
}

# GPU Configuration
GPU_CONFIG = {
    "use_gpu": False,  # Will be auto-detected
    "cuda_available": False,
    "mps_available": False,  # macOS Metal Performance Shaders
}

# UI Configuration
UI_CONFIG = {
    "window_title": "Voice-to-Voice Translator (RU → EN)",
    "window_width": 900,
    "window_height": 700,
    "theme": "default",
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "app.log",
    "max_bytes": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5,
}
