"""Setup script for Voice-to-Voice Translator"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="voice-to-voice-translator",
    version="1.0.0",
    author="Voice Translator Team",
    description="Offline voice-to-voice translator from Russian to English with voice cloning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/voicechanger",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt6>=6.6.0",
        "faster-whisper>=0.10.0",
        "transformers>=4.36.0",
        "torch>=2.1.0",
        "TTS>=0.22.0",
        "ffmpeg-python>=0.2.0",
        "librosa>=0.10.1",
        "soundfile>=0.12.1",
        "numpy>=1.24.0",
        "tqdm>=4.66.0",
    ],
    entry_points={
        "console_scripts": [
            "voice-translator=main:main",
        ],
    },
    include_package_data=True,
)
