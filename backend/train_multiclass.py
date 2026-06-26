"""
Train the multi-class payload classifier for ACSTD.

Classes: benign | sql_injection | xss | path_traversal | command_injection

- Features : TF-IDF character n-grams (same family as the existing model).
- Model    : RandomForestClassifier (the deliverable), with a LogisticRegression
             baseline trained alongside for an honest comparison.
- Output   : model_multiclass.pkl  (RF pipeline — string in, class out)
             metrics_multiclass.json  (per-class P/R/F1, accuracy, macro-F1,
                                        confusion matrix for both models)
             feature_importance.json  (RF global top n-grams + linear per-class)

IMPORTANT: this writes NEW artifacts. It never touches model.pkl, so the
existing detector stays operational until the new model is verified + wired in.

Usage:
    cd backend
    python build_multiclass_dataset.py     # if data/multiclass_dataset.csv is missing
    python train_multiclass.py
"""
import json
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data", "multiclass_dataset.csv")
MODEL_OUT = os.path.join(HERE, "model_multiclass.pkl")
METRICS_OUT = os.path.join(HERE, "metrics_multiclass.json")
FEATIMP_OUT = os.path.join(HERE, "feature_importance.json")

LABELS = ["benign", "sql_injection", "xss", "path_traversal", "command_injection"]


def _vectorizer():
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5),
                           max_features=5000, sublinear_tf=True)


def _evaluate(name, model, X_test, y_test):
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, labels=LABELS, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=LABELS).tolist()
    acc = round(accuracy_score(y_test, y_pred) * 100, 2)
    macro_f1 = round(f1_score(y_test, y_pred, labels=LABELS, average="macro", zero_division=0) * 100, 2)

    print(f"\n=== {name} ===")
    print(classification_report(y_test, y_pred, labels=LABELS, zero_division=0))
    print(f"accuracy={acc}%   macro-F1={macro_f1}%")
    print("Confusion matrix (rows=actual, cols=predicted):")
    print("actual \\ pred  " + "  ".join(f"{l[:6]:>6}" for l in LABELS))
    for l, row in zip(LABELS, cm):
        print(f"  {l:<16}" + "  ".join(f"{v:>6}" for v in row))

    per_class = {l: {"precision": round(report[l]["precision"] * 100, 2),
                     "recall": round(report[l]["recall"] * 100, 2),
                     "f1": round(report[l]["f1-score"] * 100, 2),
                     "support": int(report[l]["support"])} for l in LABELS}
    return {"accuracy": acc, "macro_f1": macro_f1,
            "per_class": per_class, "confusion_matrix": cm}


def main():
    print(f"Loading {DATA} ...")
    df = pd.read_csv(DATA, encoding="utf-8").dropna()
    df["payload"] = df["payload"].astype(str)
    X, y = df["payload"].tolist(), df["label"].tolist()
    print(f"  rows: {len(df)}   classes: {df['label'].value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y)
    print(f"  train={len(X_train)}  test={len(X_test)}")

    rf = Pipeline([
        ("tfidf", _vectorizer()),
        ("clf", RandomForestClassifier(
            n_estimators=200, n_jobs=-1, class_weight="balanced", random_state=42)),
    ])
    lin = Pipeline([
        ("tfidf", _vectorizer()),
        ("clf", LogisticRegression(
            C=5.0, max_iter=1000, class_weight="balanced")),
    ])

    print("\nTraining RandomForest ...")
    rf.fit(X_train, y_train)
    print("Training LogisticRegression baseline ...")
    lin.fit(X_train, y_train)

    rf_metrics = _evaluate("RandomForest (deliverable)", rf, X_test, y_test)
    lin_metrics = _evaluate("LogisticRegression (baseline)", lin, X_test, y_test)

    # ── feature importance ──────────────────────────────────────────────────
    names = rf.named_steps["tfidf"].get_feature_names_out()
    rf_imp = rf.named_steps["clf"].feature_importances_
    top_idx = np.argsort(rf_imp)[::-1][:25]
    rf_top = [{"ngram": names[i], "importance": round(float(rf_imp[i]), 5)} for i in top_idx]

    lin_clf = lin.named_steps["clf"]
    lin_per_class = {}
    for ci, label in enumerate(lin_clf.classes_):
        coefs = lin_clf.coef_[ci]
        top = np.argsort(coefs)[::-1][:12]
        lin_per_class[str(label)] = [{"ngram": names[i], "weight": round(float(coefs[i]), 3)} for i in top]

    print("\n=== RandomForest — top 15 n-grams by importance ===")
    for f in rf_top[:15]:
        print(f"  {f['ngram']!r:<12} {f['importance']}")

    # ── persist (new artifacts only — model.pkl untouched) ──────────────────
    with open(MODEL_OUT, "wb") as f:
        pickle.dump(rf, f)
    with open(METRICS_OUT, "w") as f:
        json.dump({
            "classes": LABELS,
            "dataset_rows": len(df),
            "train_size": len(X_train), "test_size": len(X_test),
            "features": "tfidf char_wb (2,5), max 5000, sublinear",
            "random_forest": rf_metrics,
            "logistic_regression": lin_metrics,
        }, f, indent=2)
    with open(FEATIMP_OUT, "w") as f:
        json.dump({"random_forest_top": rf_top, "logistic_regression_per_class": lin_per_class}, f, indent=2)

    print(f"\nSaved model   -> {MODEL_OUT}")
    print(f"Saved metrics -> {METRICS_OUT}")
    print(f"Saved feat.   -> {FEATIMP_OUT}")
    print(f"\nRF macro-F1={rf_metrics['macro_f1']}%  |  Linear macro-F1={lin_metrics['macro_f1']}%")
    print("model.pkl (existing binary model) was NOT modified.")


if __name__ == "__main__":
    main()
