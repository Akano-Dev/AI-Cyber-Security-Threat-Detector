"""Combine signature rules + ML probability into a single verdict."""
from app.detection import signatures
from app.ml import pipeline


def combined_verdict(sig_result, ml_prob: float):
    """Return (threat_type, severity, confidence_pct | None)."""
    ml_pct = round(ml_prob * 100)

    if sig_result:
        # Signature is authoritative; ML boosts or tempers confidence.
        confidence = max(ml_pct, 65) if ml_prob >= 0.5 else 65
        return sig_result["threat_type"], sig_result["severity"], confidence

    if ml_prob >= 0.70:
        # ML-only detection.
        return "Anomalous Payload", "medium", ml_pct

    return None, None, None


def evaluate(payload: str, user_agent: str):
    """Run signatures + ML and return the combined verdict tuple."""
    sig_result = signatures.analyze(payload, user_agent)
    ml_prob = pipeline.predict(payload)
    return combined_verdict(sig_result, ml_prob)
