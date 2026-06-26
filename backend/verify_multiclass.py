"""
Verify the trained multi-class model on NOVEL, hand-written payloads that the
dataset generator never produced — a real generalization check before this
model is trusted or wired into the engine. Also confirms the saved artifact
loads and exposes a clean (class, malicious_probability) interface.

Usage:
    cd backend
    python verify_multiclass.py
"""
import os
import pickle

HERE = os.path.dirname(__file__)
MODEL = os.path.join(HERE, "model_multiclass.pkl")

# (payload, expected_label) — none of these are verbatim generator output.
CASES = [
    ("GET /api/orders?status=shipped&page=3", "benign"),
    ("POST /checkout coupon=SAVE10", "benign"),
    ("how do I reset my password", "benign"),
    ("admin' OR 1=1#", "sql_injection"),
    ("1 UNION ALL SELECT NULL,version()-- -", "sql_injection"),
    ("<svg/onload=alert(String.fromCharCode(88))>", "xss"),
    ("<x onpointerover=alert(1)>", "xss"),
    ("....//....//....//etc/passwd", "path_traversal"),
    ("..%c0%af..%c0%afboot.ini", "path_traversal"),
    ("; nslookup attacker.example.com", "command_injection"),
    ("$(printf whoami)", "command_injection"),
]


def main():
    with open(MODEL, "rb") as f:
        model = pickle.load(f)
    classes = list(model.named_steps["clf"].classes_)
    benign_idx = classes.index("benign")

    print(f"Loaded {MODEL}")
    print(f"classes: {classes}\n")
    correct = 0
    print(f"{'predicted':<18} {'mal%':>5}  {'exp==pred':>9}  payload")
    print("-" * 80)
    for payload, expected in CASES:
        proba = model.predict_proba([payload])[0]
        pred = classes[proba.argmax()]
        mal = round((1 - proba[benign_idx]) * 100)
        ok = "OK" if pred == expected else "MISS"
        correct += pred == expected
        print(f"{pred:<18} {mal:>4}%  {ok:>9}  {payload[:42]}")
    print("-" * 80)
    print(f"generalization: {correct}/{len(CASES)} novel payloads correct")


if __name__ == "__main__":
    main()
