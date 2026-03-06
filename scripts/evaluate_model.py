"""Evaluate current sentiment model on a labeled validation set.

Expected CSV format (data/validation/validation.csv):
text,label
I love this!,positive
This is terrible,negative
...

Usage:
    PYTHONPATH=src python scripts/evaluate_model.py
"""
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mswia.modeling import score_text  # noqa: E402
from mswia.schemas import SentimentLabel  # noqa: E402


def load_validation(path: Path):
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text") or ""
            label = row.get("label") or ""
            if not text or not label:
                continue
            yield text, label


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    val_path = base_dir / "data" / "validation" / "validation.csv"
    if not val_path.exists():
        print(f"No validation dataset found at {val_path} – skipping evaluation.")
        return

    y_true: list[str] = []
    y_pred: list[str] = []
    for text, label in load_validation(val_path):
        out = score_text(text)
        pred = out.label.value if isinstance(out.label, SentimentLabel) else str(out.label)
        y_true.append(label)
        y_pred.append(pred)

    labels = sorted({*y_true, *y_pred})
    cm = {lbl: Counter() for lbl in labels}
    for t, p in zip(y_true, y_pred, strict=False):
        cm[t][p] += 1

    # Macro F1
    def f1_for(label: str) -> float:
        tp = cm[label][label]
        fp = sum(cm[other][label] for other in labels if other != label)
        fn = sum(cm[label][other] for other in labels if other != label)
        if tp == 0 and (fp == 0 or fn == 0):
            return 0.0
        precision = tp / (tp + fp) if tp + fp > 0 else 0.0
        recall = tp / (tp + fn) if tp + fn > 0 else 0.0
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    per_label_f1 = {lbl: f1_for(lbl) for lbl in labels}
    macro_f1 = sum(per_label_f1.values()) / len(per_label_f1) if per_label_f1 else 0.0

    report = {
        "labels": labels,
        "per_label_f1": per_label_f1,
        "macro_f1": macro_f1,
        "support": Counter(y_true),
    }

    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "model_eval_vader-baseline-1.0.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote evaluation report to {out_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

