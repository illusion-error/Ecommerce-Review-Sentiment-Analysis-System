from __future__ import annotations

import io

from fastapi.testclient import TestClient
from openpyxl import load_workbook

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
    created_date = history.json()["data"]["items"][0]["created_at"][:10]
    ranged_history = client.get(
        "/api/history",
        params={
            "page": 1,
            "page_size": 10,
            "sentiment": "positive",
            "start_time": created_date,
            "end_time": created_date,
        },
    )
    assert ranged_history.status_code == 200
    assert ranged_history.json()["data"]["total"] >= 1
    empty_history = client.get(
        "/api/history",
        params={"page": 1, "page_size": 10, "start_time": "1900-01-01", "end_time": "1900-01-01"},
    )
    assert empty_history.status_code == 200
    assert empty_history.json()["data"]["total"] == 0

    summary = client.get("/api/statistics/summary", params={"product_id": "phone"})
    assert summary.status_code == 200
    summary_data = summary.json()["data"]
    assert summary_data["total"] >= 2
    assert len(summary_data["intensity_distribution"]) == 5
    assert sum(summary_data["intensity_distribution"]) == summary_data["total"]

    exported = client.get(f"/api/export/{task_id}")
    assert exported.status_code == 200
    assert exported.content.startswith(b"\xef\xbb\xbf")
    assert "原始评论" in exported.text
    assert "情感结果" in exported.text
    assert "raw_text" not in exported.text

    exported_xlsx = client.get(f"/api/export/{task_id}", params={"file_type": "xlsx"})
    assert exported_xlsx.status_code == 200
    workbook = load_workbook(io.BytesIO(exported_xlsx.content))
    sheet = workbook["情感分析报告"]
    headers = [cell.value for cell in sheet[1]]
    assert headers[:5] == ["记录ID", "批量任务ID", "商品ID", "原始评论", "清洗后评论"]
    assert sheet.freeze_panes == "A2"
    assert sheet.column_dimensions["D"].width >= 20
