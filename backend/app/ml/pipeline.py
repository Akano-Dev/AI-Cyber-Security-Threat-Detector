"""Hybrid ML pipeline entry point.

Phase 1: delegates to the Stage-1 classical model.
Phase 4: adds the DistilBERT Stage-2 escalation for uncertain payloads here, so
no API code has to change.
"""
import json

from app.config import settings
from app.ml import classical


def load() -> bool:
    return classical.load_model()


def is_ready() -> bool:
    """True once a model is loaded (signatures still work without one)."""
    return classical.is_loaded()


def predict(payload: str) -> float:
    """Probability (0–1) that the payload is malicious."""
    return classical.predict(payload)


def model_info() -> dict:
    """Surface which models are active + saved training metrics."""
    info = {
        "stage1": {"name": "tfidf+logreg", "type": "classical", "loaded": classical.is_loaded()},
        "stage2": {"name": "distilbert", "type": "transformer", "loaded": False, "note": "added in Phase 4"},
    }
    try:
        with open(settings.metrics_path) as f:
            info["metrics"] = json.load(f)
    except Exception:
        info["metrics"] = None
    return info
