"""Translation module using NLLB (No Language Left Behind)"""
import os
import logging
from typing import List, Dict, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

from config import TRANSLATION_CONFIG, MODELS_DIR

logger = logging.getLogger(__name__)


class TranslationProcessor:
    """Handles text translation using NLLB model"""
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize translation processor
        
        Args:
            model_name: Name of the translation model
            device: Device to use (auto, cpu, cuda)
        """
        self.model_name = model_name or TRANSLATION_CONFIG["model_name"]
        self.device = device or TRANSLATION_CONFIG["device"]
        self.source_lang = TRANSLATION_CONFIG["source_lang"]
        self.target_lang = TRANSLATION_CONFIG["target_lang"]
        self.tokenizer = None
        self.model = None
        self.translator = None
        
        # Auto-detect device if set to auto
        if self.device == "auto":
            self.device = self._detect_device()
            
        logger.info(f"Initializing translation with model: {self.model_name}, device: {self.device}")
        
    def _detect_device(self) -> str:
        """Detect available device (CUDA, MPS, or CPU)"""
        if torch.cuda.is_available():
            logger.info("CUDA available, using GPU for translation")
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("MPS (Metal) available, using GPU for translation")
            return "mps"
        else:
            logger.info("No GPU available, using CPU for translation")
            return "cpu"
            
    def load_model(self):
        """Load the translation model"""
        if self.model is not None:
            logger.info("Model already loaded")
            return
            
        try:
            logger.info(f"Loading translation model: {self.model_name}")
            
            cache_dir = str(MODELS_DIR / "translation")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=cache_dir,
                src_lang=self.source_lang
            )
            
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                cache_dir=cache_dir
            )
            
            # Move model to device
            self.model.to(self.device)
            
            # Create translation pipeline
            self.translator = pipeline(
                "translation",
                model=self.model,
                tokenizer=self.tokenizer,
                src_lang=self.source_lang,
                tgt_lang=self.target_lang,
                max_length=TRANSLATION_CONFIG["max_length"],
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Translation model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading translation model: {e}")
            raise
            
    def translate_text(self, text: str) -> str:
        """
        Translate a single text string
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text
        """
        if self.translator is None:
            self.load_model()
            
        if not text or not text.strip():
            return ""
            
        try:
            logger.info(f"Translating text: {text[:50]}...")
            
            result = self.translator(
                text,
                max_length=TRANSLATION_CONFIG["max_length"],
                num_beams=TRANSLATION_CONFIG["num_beams"]
            )
            
            translated_text = result[0]['translation_text']
            logger.info(f"Translation result: {translated_text[:50]}...")
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            raise
            
    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate segments with timing information
        
        Args:
            segments: List of segment dictionaries from ASR
            
        Returns:
            List of segments with translated text
        """
        if self.translator is None:
            self.load_model()
            
        logger.info(f"Translating {len(segments)} segments")
        
        translated_segments = []
        
        for i, segment in enumerate(segments):
            try:
                original_text = segment["text"]
                
                if not original_text or not original_text.strip():
                    translated_segments.append({
                        **segment,
                        "original_text": original_text,
                        "translated_text": ""
                    })
                    continue
                
                # Translate
                translated_text = self.translate_text(original_text)
                
                # Create new segment with translation
                translated_segment = {
                    **segment,
                    "original_text": original_text,
                    "translated_text": translated_text
                }
                
                translated_segments.append(translated_segment)
                
                logger.info(f"Segment {i+1}/{len(segments)}: '{original_text}' -> '{translated_text}'")
                
            except Exception as e:
                logger.error(f"Error translating segment {i}: {e}")
                # Keep original in case of error
                translated_segments.append({
                    **segment,
                    "original_text": segment["text"],
                    "translated_text": segment["text"]
                })
        
        logger.info(f"Translation completed for {len(translated_segments)} segments")
        return translated_segments
        
    def translate_with_context(self, segments: List[Dict], context_window: int = 2) -> List[Dict]:
        """
        Translate segments with context from surrounding segments for better quality
        
        Args:
            segments: List of segment dictionaries from ASR
            context_window: Number of segments before/after to use as context
            
        Returns:
            List of segments with translated text
        """
        if self.translator is None:
            self.load_model()
            
        logger.info(f"Translating {len(segments)} segments with context window: {context_window}")
        
        translated_segments = []
        
        for i, segment in enumerate(segments):
            try:
                # Get context
                start_idx = max(0, i - context_window)
                end_idx = min(len(segments), i + context_window + 1)
                
                # Build context text
                context_texts = [s["text"] for s in segments[start_idx:end_idx]]
                context_text = " ".join(context_texts)
                
                # Translate with context
                translated_context = self.translate_text(context_text)
                
                # Extract the relevant translation (simplified approach)
                # In production, you might want more sophisticated extraction
                original_text = segment["text"]
                
                # For now, just translate the individual segment
                # Context helps the model understand better, but we still extract per-segment
                translated_text = self.translate_text(original_text)
                
                translated_segment = {
                    **segment,
                    "original_text": original_text,
                    "translated_text": translated_text
                }
                
                translated_segments.append(translated_segment)
                
                logger.info(f"Segment {i+1}/{len(segments)}: '{original_text}' -> '{translated_text}'")
                
            except Exception as e:
                logger.error(f"Error translating segment {i} with context: {e}")
                translated_segments.append({
                    **segment,
                    "original_text": segment["text"],
                    "translated_text": segment["text"]
                })
        
        return translated_segments
        
    def save_translation(self, segments: List[Dict], output_path: str):
        """
        Save translation to file
        
        Args:
            segments: List of translated segments
            output_path: Path to output file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for segment in segments:
                    f.write(f"[{segment['start']:.2f}s - {segment['end']:.2f}s]\n")
                    f.write(f"Original: {segment['original_text']}\n")
                    f.write(f"Translation: {segment['translated_text']}\n")
                    f.write("\n")
            logger.info(f"Translation saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving translation: {e}")
            raise
            
    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            logger.info("Unloading translation model")
            del self.model
            del self.tokenizer
            del self.translator
            self.model = None
            self.tokenizer = None
            self.translator = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
