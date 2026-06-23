"""
Train the ML model from a CSV dataset and save model.pkl + metrics.json.

Usage:
    cd backend
    python train.py

Expected CSV: data/sqli_dataset.csv
  - Text column : "Query" or "Sentence"
  - Label column: "Label"  (0 = safe, 1 = malicious)
"""

import json
import os
import pickle

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

CSV_PATH     = os.path.join(os.path.dirname(__file__), "data", "sqli_dataset.csv")
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "model.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "metrics.json")


# ── 1. Load dataset ────────────────────────────────────────────────────────

print(f"Loading {CSV_PATH} ...")
df = pd.read_csv(CSV_PATH, encoding="utf-8")

# Auto-detect text column ("Query" per user spec; "Sentence" in SQLiV3.csv from Kaggle)
if "Query" in df.columns:
    text_col = "Query"
elif "Sentence" in df.columns:
    text_col = "Sentence"
else:
    raise ValueError(f"No text column found. Got: {list(df.columns)}")

print(f"  Text column : '{text_col}'")
print(f"  Rows before cleaning: {len(df)}")

df = df[[text_col, "Label"]].dropna()
df["Label"] = df["Label"].astype(str).str.strip()
df = df[df["Label"].isin(["0", "1"])]
df["Label"] = df["Label"].astype(int)
df[text_col] = df[text_col].astype(str)

print(f"  Rows after cleaning : {len(df)}")
print(f"  Label distribution  : {df['Label'].value_counts().to_dict()}")

X = df[text_col].tolist()
y = df["Label"].tolist()


# ── 2. Train / test split ──────────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train)}  |  Test: {len(X_test)}")


# ── 3. Build and train pipeline ────────────────────────────────────────────

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        max_features=8000,
        sublinear_tf=True,
    )),
    ("clf", LogisticRegression(C=5.0, max_iter=1000, n_jobs=-1)),
])

print("Training ...")
model.fit(X_train, y_train)


# ── 4. Evaluate ────────────────────────────────────────────────────────────

y_pred = model.predict(X_test)

acc  = round(accuracy_score(y_test, y_pred)  * 100, 2)
prec = round(precision_score(y_test, y_pred) * 100, 2)
rec  = round(recall_score(y_test, y_pred)    * 100, 2)
f1   = round(f1_score(y_test, y_pred)        * 100, 2)
cm   = confusion_matrix(y_test, y_pred).tolist()

print("\n" + classification_report(y_test, y_pred, target_names=["normal", "malicious"]))
print("Confusion matrix (rows=actual, cols=predicted):")
print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
print(f"  FN={cm[1][0]}  TP={cm[1][1]}")


# ── 5. Save model + metrics ────────────────────────────────────────────────

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)
print(f"\nSaved model   → {MODEL_PATH}")

metrics = {
    "dataset_rows": len(df),
    "train_size":   len(X_train),
    "test_size":    len(X_test),
    "accuracy":     acc,
    "precision":    prec,
    "recall":       rec,
    "f1":           f1,
    "confusion_matrix": {
        "TN": cm[0][0], "FP": cm[0][1],
        "FN": cm[1][0], "TP": cm[1][1],
    },
}

with open(METRICS_PATH, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"Saved metrics → {METRICS_PATH}")
print(f"\nAccuracy={acc}%  Precision={prec}%  Recall={rec}%  F1={f1}%")
