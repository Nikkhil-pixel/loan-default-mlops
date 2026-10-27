"""Shared model scoring and artifact helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def classification_metrics(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    """Compute probability ranking and threshold-specific metrics."""
    from sklearn.metrics import auc

    predictions = (probabilities >= threshold).astype(int)
    fpr, tpr, _ = roc_curve(y_true, probabilities)
    precision_curve, recall_curve, _ = precision_recall_curve(y_true, probabilities)
    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "ks_statistic": float(np.max(tpr - fpr)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, predictions).tolist(),
        "roc_curve_auc": float(auc(fpr, tpr)),
        "roc_curve": (fpr, tpr),
        "pr_curve": (recall_curve, precision_curve),
    }


def log_evaluation_artifacts(metrics: dict[str, Any], artifact_dir: Path) -> None:
    """Write ROC and PR charts plus a JSON confusion-matrix artifact."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for name, x, y, xlabel, ylabel in (
        ("roc_curve.png", metrics["roc_curve"][0], metrics["roc_curve"][1], "False positive rate", "True positive rate"),
        ("precision_recall_curve.png", metrics["pr_curve"][0], metrics["pr_curve"][1], "Recall", "Precision"),
    ):
        fig, axis = plt.subplots()
        axis.plot(x, y)
        axis.set(xlabel=xlabel, ylabel=ylabel, title=name.replace("_", " ").removesuffix(".png"))
        fig.tight_layout()
        fig.savefig(artifact_dir / name)
        plt.close(fig)
    (artifact_dir / "confusion_matrix.json").write_text(
        json.dumps(metrics["confusion_matrix"], indent=2), encoding="utf-8"
    )
