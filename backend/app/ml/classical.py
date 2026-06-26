"""Stage-1 fast classical model (TF-IDF + linear classifier).

Currently the existing binary SQLi model. Phase 3 replaces model.pkl with a
multi-class model; this loader stays the same.
"""
import os
import pickle

from app.config import settings

_model = None


def load_model() -> bool:
    global _model
    if not os.path.exists(settings.model_path):
        return False
    with open(settings.model_path, "rb") as f:
        _model = pickle.load(f)
    return True


def is_loaded() -> bool:
    return _model is not None


def predict(payload: str) -> float:
    """Probability (0–1) that the payload is malicious."""
    if _model is None:
        return 0.5
    return float(_model.predict_proba([payload])[0][1])
