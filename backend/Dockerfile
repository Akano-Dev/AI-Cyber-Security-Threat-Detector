# ACSTD backend — production image (FastAPI API + Swagger UI).
# Builds a self-contained image that bakes the ML model so the detector's
# ML half works out of the box. Signatures work even without it.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

# Python deps first (scikit-learn / pandas ship prebuilt wheels — no compiler needed).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source + training data.
COPY app ./app
COPY data ./data
COPY train.py demo_site.py simulate_traffic.py ./
COPY simulator ./simulator

# Bake the Stage-1 model from the tracked dataset (best-effort; safe to skip).
RUN python train.py || echo "WARNING: model training skipped — signatures only."

# Hugging Face Spaces (and good practice) run containers as a non-root uid 1000.
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Write runtime artifacts inside the writable app dir.
ENV DB_PATH=/app/threats.db \
    MODEL_PATH=/app/model.pkl \
    METRICS_PATH=/app/metrics.json

EXPOSE 7860
# Shell form so ${PORT} (overridable by the platform) is expanded.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
