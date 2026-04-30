import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for the zero-shot pipeline to avoid loading the model multiple times
_zero_shot_classifier = None

def get_classifier():
    global _zero_shot_classifier
    if _zero_shot_classifier is None:
        try:
            from transformers import pipeline
            # Using a lightweight multilingual model that understands context in PT-BR
            logger.info("Loading Zero-Shot Classification model (this might take a while on the first run)...")
            _zero_shot_classifier = pipeline(
                "zero-shot-classification", 
                model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
            )
            logger.info("Zero-Shot model loaded successfully.")
        except ImportError:
            logger.warning("Transformers library not installed. Falling back to keyword matching.")
            return None
        except Exception as e:
            logger.error(f"Failed to load Zero-Shot model: {e}")
            return None
    return _zero_shot_classifier

def suggest_labels_deterministic(text_lower: str, available_labels: list[dict]) -> list[str]:
    """Fallback logic using simple keyword matching."""
    suggested_ids = []
    for label in available_labels:
        label_name = label["name"].lower()
        
        pattern = rf"\b{re.escape(label_name)}\b"
        if re.search(pattern, text_lower):
            suggested_ids.append(label["id"])
            continue
            
        if label_name == "cliente" and any(word in text_lower for word in ["parceiro", "contrato", "fechar"]):
             suggested_ids.append(label["id"])
        elif label_name == "orçamento" and any(word in text_lower for word in ["preço", "valor", "reais", "custo"]):
             suggested_ids.append(label["id"])
        elif label_name == "urgente" and any(word in text_lower for word in ["asap", "prazo", "agora", "rápido"]):
             suggested_ids.append(label["id"])
             
    return suggested_ids

def suggest_labels(transcript_text: str, available_labels: list[dict]) -> list[str]:
    """
    Suggests labels based on zero-shot context classification (if transformers is available),
    otherwise falls back to keywords in the transcript.
    """
    if not transcript_text or not available_labels:
        return []

    classifier = get_classifier()
    suggested_ids = set()

    if classifier:
        # Contextual AI Path (Zero-Shot)
        label_names = [label["name"] for label in available_labels]
        
        # We take the last 2000 chars to avoid hitting token limits (usually ~512 tokens for DeBERTa)
        # In a real app, we could chunk the transcript, but taking the tail or a sample is often enough
        text_to_analyze = transcript_text[-2500:] 
        
        try:
            # multi_label=True allows multiple classes to be independent
            result = classifier(text_to_analyze, candidate_labels=label_names, multi_label=True)
            
            # Result contains 'labels' and 'scores' sorted by score
            for label_name, score in zip(result["labels"], result["scores"]):
                if score > 0.65:  # 65% confidence threshold
                    # Find the corresponding ID
                    for lbl in available_labels:
                        if lbl["name"] == label_name:
                            suggested_ids.add(lbl["id"])
                            break
                            
            # Add fallback to ensure we don't miss obvious keyword matches
            suggested_ids.update(suggest_labels_deterministic(transcript_text.lower(), available_labels))
            
        except Exception as e:
            logger.error(f"Error during zero-shot classification: {e}")
            suggested_ids.update(suggest_labels_deterministic(transcript_text.lower(), available_labels))
    else:
        # Fallback Deterministic Path
        suggested_ids.update(suggest_labels_deterministic(transcript_text.lower(), available_labels))

    return list(suggested_ids)
