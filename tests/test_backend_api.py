from __future__ import annotations

import io

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_single_analysis_and_cache_hit():
    payload = {"text": "物流很快，质量不错，下次还会买", "product_id": "phone"}
    first = client.post("/api/sentiment/single", json=payload)
    second = client.post("/api/sentiment/single", json=payload)

    assert first.status_code == 200
    assert first.json()["data"]["sentiment"] == "positive"
    assert second.status_code == 200
    assert second.json()["data"]["cached"] is True


def test_batch_history_summary_and_export():
    csv_bytes = "content,product_id\n很好用,phone\n垃圾质量,phone\n".encode("utf-8-sig")
    response = client.post(
        "/api/sentiment/batch",
        files={"file": ("comments.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"product_id": "phone"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert data["success_count"] == 2
    assert data["positive_count"] >= 1
    assert data["negative_count"] >= 1
    task_id = data["task_id"]

    task = client.get(f"/api/tasks/{task_id}")
    assert task.status_code == 200
    assert task.json()["data"]["status"] == "completed"

    history = client.get("/api/history", params={"page": 1, "page_size": 10, "sentiment": "positive"})
    assert history.status_code == 200
    assert history.json()["data"]["total"] >= 1

    summary = client.get("/api/statistics/summary", params={"product_id": "phone"})
    assert summary.status_code == 200
    assert summary.json()["data"]["total"] >= 2

    exported = client.get(f"/api/export/{task_id}")
    assert exported.status_code == 200
    assert "raw_text" in exported.text

