"""Second-stage sentiment performance evaluation.

Run manually with:

    python model/performance_test.py

This script intentionally uses `backend.sentiment.predict_sentiment`, which
falls back to the deterministic lexicon baseline when local BERT weights or
torch are unavailable. That makes the report reproducible in the lightweight
API/Docker environment while still exercising the same prediction contract used
by FastAPI.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT_JSON = ROOT / "reports" / "model_performance_report.json"
REPORT_MD = ROOT / "reports" / "model_performance_report.md"

from backend.sentiment import predict_sentiment


def _label_from_row(row: Dict[str, Any]) -> int | None:
    if "label" in row and pd.notna(row["label"]):
        return int(row["label"])
    if "star" in row and pd.notna(row["star"]):
        star = int(row["star"])
        if star >= 4:
            return 1
        if star <= 2:
            return 0
    return None


def _load_dataset(name: str, path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"name": name, "path": str(path), "items": [], "skipped": 0}
    df = pd.read_csv(path)
    items: List[Dict[str, Any]] = []
    skipped = 0
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        label = _label_from_row(row_dict)
        text = str(row_dict.get("clean_content") or row_dict.get("content") or "").strip()
        if label is None or not text:
            skipped += 1
            continue
        items.append({"text": text, "label": label})
    return {"name": name, "path": str(path), "items": items, "skipped": skipped}


def _binary_metrics(true_labels: List[int], pred_labels: List[int]) -> Dict[str, Any]:
    tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(true_labels, pred_labels) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(true_labels, pred_labels) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == 1 and p == 0)
    total = len(true_labels)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def _latency_stats(times: List[float]) -> Dict[str, Any]:
    if not times:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "p95_ms": 0, "total_seconds": 0, "throughput_per_sec": 0}
    sorted_times = sorted(times)
    p95_index = min(len(sorted_times) - 1, max(0, math.ceil(len(sorted_times) * 0.95) - 1))
    total = sum(times)
    return {
        "avg_ms": round(total / len(times) * 1000, 2),
        "min_ms": round(min(times) * 1000, 2),
        "max_ms": round(max(times) * 1000, 2),
        "p95_ms": round(sorted_times[p95_index] * 1000, 2),
        "total_seconds": round(total, 4),
        "throughput_per_sec": round(len(times) / total, 2) if total else 0,
    }


def evaluate_dataset(dataset: Dict[str, Any]) -> Dict[str, Any]:
    pred_labels: List[int] = []
    true_labels: List[int] = []
    confidences: List[float] = []
    times: List[float] = []

    for item in dataset["items"]:
        start = time.perf_counter()
        prediction = predict_sentiment(item["text"])
        elapsed = time.perf_counter() - start
        true_labels.append(int(item["label"]))
        pred_labels.append(int(prediction["label"]))
        confidences.append(float(prediction.get("confidence", 0.0)))
        times.append(elapsed)

    return {
        "name": dataset["name"],
        "path": dataset["path"],
        "total_samples": len(true_labels),
        "positive_samples": sum(true_labels),
        "negative_samples": len(true_labels) - sum(true_labels),
        "skipped_samples": int(dataset["skipped"]),
        "metrics": _binary_metrics(true_labels, pred_labels),
        "performance": _latency_stats(times),
        "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
    }


def build_report() -> Dict[str, Any]:
    datasets = [
        _load_dataset("processed_test", ROOT / "data" / "processed" / "test.csv"),
        _load_dataset("demo_comments", ROOT / "data" / "demo" / "demo_comments.csv"),
    ]
    results = [evaluate_dataset(dataset) for dataset in datasets]
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "predictor": "backend.sentiment.predict_sentiment",
        "mode": "bert_or_rule_fallback",
        "datasets": results,
    }


def write_report(report: Dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# 模型性能复测报告",
        "",
        f"**测试时间**：{report['timestamp']}",
        "",
        "## 1. 测试说明",
        "",
        "本报告使用后端实际调用的 `backend.sentiment.predict_sentiment` 进行复测。"
        "如果本地缺少 BERT 权重或 torch，系统会自动使用规则兜底模型，因此该结果可在轻量后端环境复现。",
        "",
        "## 2. 指标结果",
        "",
        "| 测试集 | 样本数 | 跳过样本 | Accuracy | Precision | Recall | F1 | 平均耗时 | P95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report["datasets"]:
        metrics = item["metrics"]
        perf = item["performance"]
        lines.append(
            f"| {item['name']} | {item['total_samples']} | {item['skipped_samples']} | "
            f"{metrics['accuracy']:.4f} | {metrics['precision']:.4f} | {metrics['recall']:.4f} | "
            f"{metrics['f1']:.4f} | {perf['avg_ms']:.2f} ms | {perf['p95_ms']:.2f} ms |"
        )
    lines.extend(
        [
            "",
            "## 3. 混淆矩阵",
            "",
            "| 测试集 | TN | FP | FN | TP |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in report["datasets"]:
        cm = item["metrics"]["confusion_matrix"]
        lines.append(f"| {item['name']} | {cm['tn']} | {cm['fp']} | {cm['fn']} | {cm['tp']} |")
    lines.extend(
        [
            "",
            "## 4. 结论",
            "",
            "当前结果用于验证第二阶段系统性能口径和可复现流程。后续如果接入完整 BERT 权重，可再次运行本脚本刷新报告。",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    report = build_report()
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport written to {REPORT_MD}")


if __name__ == "__main__":
    main()
