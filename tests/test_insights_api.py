from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _post_review(text: str, product_id: str):
    response = client.post(
        "/api/sentiment/single",
        json={"text": text, "product_id": product_id, "comment_time": "2026-07-13"},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_insight_keywords_aspects_and_summary():
    product_id = f"insight-{uuid.uuid4().hex[:8]}"
    _post_review("物流很快，包装很好，质量不错，价格也很划算", product_id)
    _post_review("质量很差，包装破损，价格太贵，发货慢", product_id)
    _post_review("做工精致，材质舒服，性价比高，推荐购买", product_id)

    keywords = client.get("/api/insights/keywords", params={"product_id": product_id, "top_k": 10})
    assert keywords.status_code == 200
    keyword_data = keywords.json()["data"]
    assert keyword_data["record_count"] == 3
    assert keyword_data["positive_words"]
    assert keyword_data["negative_words"]
    assert any(item["word"] in {"物流", "质量", "包装", "划算", "性价比"} for item in keyword_data["positive_words"])
    assert any(item["word"] in {"破损", "太贵", "发货慢", "质量差", "包装"} for item in keyword_data["negative_words"])

    aspects = client.get("/api/insights/aspects", params={"product_id": product_id})
    assert aspects.status_code == 200
    aspect_data = aspects.json()["data"]
    assert aspect_data["record_count"] == 3
    aspect_map = {item["name"]: item for item in aspect_data["aspects"]}
    assert set(aspect_map) == {"价格", "物流", "质量"}
    assert aspect_map["价格"]["total_count"] >= 2
    assert aspect_map["物流"]["total_count"] >= 2
    assert aspect_map["质量"]["total_count"] >= 2
    assert 0 <= aspect_map["质量"]["score"] <= 100

    summary = client.get("/api/summary/product", params={"product_id": product_id})
    assert summary.status_code == 200
    summary_data = summary.json()["data"]
    assert summary_data["mode"] == "rule_fallback"
    assert summary_data["advantages"]
    assert summary_data["disadvantages"]
    assert summary_data["buying_advice"]
    assert "aspect_scores" in summary_data["evidence"]


def test_insight_empty_data_returns_stable_shape():
    product_id = f"empty-{uuid.uuid4().hex[:8]}"

    keywords = client.get("/api/insights/keywords", params={"product_id": product_id})
    assert keywords.status_code == 200
    assert keywords.json()["data"]["positive_words"] == []
    assert keywords.json()["data"]["negative_words"] == []

    aspects = client.get("/api/insights/aspects", params={"product_id": product_id})
    assert aspects.status_code == 200
    for item in aspects.json()["data"]["aspects"]:
        assert item["status"] == "no_data"
        assert item["score"] == 0.0

    summary = client.get("/api/summary/product", params={"product_id": product_id})
    assert summary.status_code == 200
    assert summary.json()["data"]["record_count"] == 0
