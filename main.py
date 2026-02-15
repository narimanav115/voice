"""
Voice-to-Voice Translator (RU → EN)
Offline desktop application for translating Russian speech to English while preserving voice characteristics.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import LOGGING_CONFIG, LOGS_DIR
from src.ui.main_window import main as run_gui


def setup_logging():
    """Setup application logging"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=LOGGING_CONFIG["level"],
        format=LOGGING_CONFIG["format"],
        handlers=[
            logging.FileHandler(LOGGING_CONFIG["file"]),
            logging.StreamHandler()
        ]
    )


def main():
    """Main entry point"""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Voice-to-Voice Translator application")
        
        # Check ffmpeg availability
        try:
            import ffmpeg
            logger.info("ffmpeg-python is available")
        except ImportError:
            logger.warning("ffmpeg-python not found. Install it with: pip install ffmpeg-python")
            logger.warning("Also ensure ffmpeg is installed on your system")
        
        # Run GUI
        run_gui()
        
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
