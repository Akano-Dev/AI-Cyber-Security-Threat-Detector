"""
Train and save the ML model from a real dataset.

Usage:
    python train.py

Expects: backend/data/sqli_dataset.csv  (columns: Query, Label)
Outputs: model.pkl, metrics.json
"""
import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# ── load data ─────────────────────────────────────────────────────────────

CSV_PATH = Path(__file__).parent / "data" / "sqli_dataset.csv"

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

# Normalise column names — handle minor variations in the CSV header
df.columns = df.columns.str.strip()
if "Query" not in df.columns or "Label" not in df.columns:
    raise ValueError(f"Expected columns 'Query' and 'Label'. Found: {list(df.columns)}")

df = df.dropna(subset=["Query", "Label"])
df["Label"] = df["Label"].astype(int)

X = df["Query"].astype(str).tolist()
y = df["Label"].tolist()

print(f"Dataset: {len(X)} samples  |  malicious={sum(y)}  normal={len(y)-sum(y)}")

# ── split ──────────────────────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── train ──────────────────────────────────────────────────────────────────

model = Pipeline([
    ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), max_features=10000)),
    ("clf",   LogisticRegression(C=5.0, max_iter=1000, class_weight="balanced")),
])

model.fit(X_train, y_train)
y_pred = model.predict(y_test if False else X_test)   # X_test

# ── metrics ────────────────────────────────────────────────────────────────

acc  = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec  = recall_score(y_test, y_pred)
f1   = f1_score(y_test, y_pred)
cm   = confusion_matrix(y_test, y_pred).tolist()

report = classification_report(y_test, y_pred, target_names=["normal", "malicious"])
print("\n" + report)
print(f"Confusion matrix:\n  TN={cm[0][0]}  FP={cm[0][1]}\n  FN={cm[1][0]}  TP={cm[1][1]}\n")

metrics = {
    "train_samples": len(X_train),
    "test_samples":  len(X_test),
    "accuracy":      round(acc,  4),
    "precision":     round(prec, 4),
    "recall":        round(rec,  4),
    "f1":            round(f1,   4),
    "confusion_matrix": {"TN": cm[0][0], "FP": cm[0][1], "FN": cm[1][0], "TP": cm[1][1]},
}

metrics_path = Path(__file__).parent / "metrics.json"
metrics_path.write_text(json.dumps(metrics, indent=2))
print(f"Metrics saved → {metrics_path}")

# ── save model ─────────────────────────────────────────────────────────────

model_path = Path(__file__).parent / "model.pkl"
with open(model_path, "wb") as f:
    pickle.dump(model, f)
print(f"Model saved  → {model_path}")
