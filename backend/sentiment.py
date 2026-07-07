"""Sentiment prediction service.

This module gives member B a stable backend dependency while member C develops
the real BERT model. If `model.predict.predict_sentiment` exists, the backend
uses it. Otherwise it falls back to a deterministic lexicon baseline so every
API endpoint can be tested immediately.
"""

from __future__ import annotations

import re
from typing import Any, Dict


POSITIVE_WORDS = {
    "好",
    "很好",
    "不错",
    "满意",
    "喜欢",
    "推荐",
    "快",
    "舒服",
    "精致",
    "正品",
    "划算",
    "值得",
    "beautiful",
    "good",
    "great",
}

NEGATIVE_WORDS = {
    "差",
    "很差",
    "失望",
    "垃圾",
    "慢",
    "难用",
    "破损",
    "退货",
    "不好",
    "一般",
    "假货",
    "糟糕",
    "bad",
    "poor",
}


def clean_text(text: str) -> str:
    """Clean review text using the project requirement pipeline."""

    text = re.sub(r"https?://\S+|www\.\S+", "", text or "")
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)
    return text.strip()


def _rule_based_predict(text: str) -> Dict[str, Any]:
    """Small deterministic baseline used before the BERT model is connected."""

    clean = clean_text(text)
    lower = clean.lower()
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in clean or word in lower)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in clean or word in lower)
    score = positive_hits - negative_hits
    if score >= 0:
        label = 1
        sentiment = "positive"
    else:
        label = 0
        sentiment = "negative"
    confidence = min(0.98, 0.55 + abs(score) * 0.12)
    strength = round(confidence * 10 if label == 1 else (1 - confidence) * 10, 2)
    return {
        "text": text,
        "clean_text": clean,
        "label": label,
        "sentiment": sentiment,
        "confidence": round(confidence, 4),
        "strength": strength,
    }


def predict_sentiment(text: str) -> Dict[str, Any]:
    """Predict sentiment for one review.

    The expected C-side model function may return either this project's field
    names or a minimal `label/confidence` pair. This wrapper normalizes both.
    """

    try:
        from model.predict import predict_sentiment as bert_predict

        output = bert_predict(text)
        clean = output.get("clean_text") or clean_text(text)
        label = int(output.get("label", 1))
        sentiment = output.get("sentiment") or ("positive" if label == 1 else "negative")
        confidence = float(output.get("confidence", 0.5))
        strength = float(output.get("strength", round(confidence * 10 if label == 1 else (1 - confidence) * 10, 2)))
        return {
            "text": text,
            "clean_text": clean,
            "label": label,
            "sentiment": sentiment,
            "confidence": round(confidence, 4),
            "strength": round(strength, 2),
        }
    except Exception:
        return _rule_based_predict(text)

