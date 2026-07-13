"""Model package helpers.

Keep this package lightweight on import. The FastAPI service imports
`model.text_insights` in the API-only Docker image, where `torch` is not
installed. BERT inference is therefore loaded lazily only when callers use the
prediction helpers below.
"""

from __future__ import annotations

from typing import Any


def predict_sentiment(text: str) -> dict[str, Any]:
    from .predict import predict_sentiment as _predict_sentiment

    return _predict_sentiment(text)


def predict_batch(texts: list[str]) -> list[dict[str, Any]]:
    from .predict import predict_batch as _predict_batch

    return _predict_batch(texts)
