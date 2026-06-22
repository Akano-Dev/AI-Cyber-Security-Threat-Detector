import os
import pickle

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
_model = None


def load_model() -> bool:
    global _model
    if not os.path.exists(MODEL_PATH):
        return False
    with open(MODEL_PATH, "rb") as f:
        _model = pickle.load(f)
    return True


def predict(payload: str) -> float:
    """Return probability (0–1) that the payload is malicious."""
    if _model is None:
        return 0.5
    return float(_model.predict_proba([payload])[0][1])
