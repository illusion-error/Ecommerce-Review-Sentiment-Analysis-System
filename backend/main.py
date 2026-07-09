"""FastAPI backend for e-commerce review sentiment analysis."""

from __future__ import annotations

import csv
import io
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .cache import prediction_cache
from .database import (
    create_batch_task,
    get_batch_task,
    init_db,
    insert_analysis_record,
    list_history,
    records_by_task,
    summary_statistics,
)
from .schemas import SingleSentimentRequest
from .sentiment import predict_sentiment
from .settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make direct TestClient usage and local scripts stable even when lifespan hooks
# are not entered explicitly. `startup()` keeps the same initialization for
# normal uvicorn runs, and SQLite `CREATE TABLE IF NOT EXISTS` is idempotent.
init_db()


def api_response(data: Any = None, message: str = "ok", code: int = 0, success: bool = True) -> Dict[str, Any]:
    return {"success": success, "message": message, "data": data, "code": code}


def _analyze_and_store(
    text: str,
    *,
    product_id: str = "",
    task_id: str = "",
    comment_time: str = "",
) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("评论文本不能为空")

    cached_value = prediction_cache.get(text)
    cached = cached_value is not None
    result = cached_value if cached_value is not None else predict_sentiment(text)
    if not cached:
        prediction_cache.set(text, result)

    stored = insert_analysis_record(
        task_id=task_id,
        product_id=product_id,
        raw_text=text,
        clean_text=result["clean_text"],
        label=int(result["label"]),
        sentiment=str(result["sentiment"]),
        confidence=float(result["confidence"]),
        strength=float(result["strength"]),
        cached=cached,
        comment_time=comment_time,
    )
    return {
        "record_id": stored["id"],
        "text": text,
        "clean_text": result["clean_text"],
        "label": int(result["label"]),
        "sentiment": str(result["sentiment"]),
        "confidence": float(result["confidence"]),
        "strength": float(result["strength"]),
        "cached": cached,
        "product_id": product_id,
    }


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return api_response(
        {
            "status": "ok",
            "version": settings.app_version,
            "database_backend": settings.database_backend,
            "cache": prediction_cache.stats(),
        },
        message="服务正常",
    )


@app.post("/api/sentiment/single")
def analyze_single(payload: SingleSentimentRequest) -> Dict[str, Any]:
    try:
        result = _analyze_and_store(
            payload.text,
            product_id=payload.product_id or "",
            comment_time=payload.comment_time or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return api_response(result, message="分析成功")


def _read_upload(file: UploadFile) -> pd.DataFrame:
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")

    filename = file.filename or ""
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    try:
        if suffix in {"xlsx", "xls"}:
            return pd.read_excel(io.BytesIO(content))
        for encoding in ("utf-8-sig", "utf-8", "gbk"):
            try:
                return pd.read_csv(io.BytesIO(content), encoding=encoding)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(io.BytesIO(content), encoding="gbk", encoding_errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {exc}") from exc


def _pick_text_column(df: pd.DataFrame) -> str:
    candidates = ["content", "comment", "text", "raw_text", "评论", "评价", "评论内容"]
    lower_map = {str(col).lower(): col for col in df.columns}
    for item in candidates:
        if item.lower() in lower_map:
            return lower_map[item.lower()]
    if len(df.columns) == 0:
        raise HTTPException(status_code=400, detail="文件没有可读取的列")
    return str(df.columns[0])


@app.post("/api/sentiment/batch")
def analyze_batch(
    file: UploadFile = File(...),
    product_id: str = Form(default=""),
) -> Dict[str, Any]:
    df = _read_upload(file)
    if len(df) > settings.max_upload_rows:
        raise HTTPException(status_code=400, detail=f"单次最多支持 {settings.max_upload_rows} 行")

    text_column = _pick_text_column(df)
    task_id = f"batch_{uuid.uuid4().hex[:12]}"
    create_batch_task(task_id, file.filename or "upload", len(df))

    results: List[Dict[str, Any]] = []
    failed_count = 0
    positive_count = 0
    negative_count = 0
    strength_sum = 0.0

    for idx, row in df.iterrows():
        row_product_id = str(row.get("product_id") or row.get("cat") or product_id or "")
        comment_time = str(row.get("comment_time") or row.get("time") or "")
        text = "" if pd.isna(row.get(text_column)) else str(row.get(text_column)).strip()
        if not text:
            failed_count += 1
            results.append({"row_index": int(idx), "success": False, "error": "评论文本为空"})
            continue
        try:
            item = _analyze_and_store(text, product_id=row_product_id, task_id=task_id, comment_time=comment_time)
            item["row_index"] = int(idx)
            item["success"] = True
            results.append(item)
            if item["sentiment"] == "positive":
                positive_count += 1
            else:
                negative_count += 1
            strength_sum += float(item["strength"])
        except Exception as exc:
            failed_count += 1
            results.append({"row_index": int(idx), "success": False, "error": str(exc)})

    success_count = len(results) - failed_count
    avg_strength = round(strength_sum / success_count, 2) if success_count else 0.0
    status = "completed" if failed_count == 0 else "completed_with_errors"
    update_error = "" if failed_count == 0 else f"{failed_count} rows failed"
    from .database import update_batch_task

    update_batch_task(
        task_id,
        status=status,
        success_count=success_count,
        failed_count=failed_count,
        positive_count=positive_count,
        negative_count=negative_count,
        avg_strength=avg_strength,
        error_message=update_error,
    )
    return api_response(
        {
            "task_id": task_id,
            "total": len(df),
            "success_count": success_count,
            "failed_count": failed_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "avg_strength": avg_strength,
            "results": results,
        },
        message="批量分析完成",
    )


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> Dict[str, Any]:
    task = get_batch_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="批量任务不存在")
    return api_response(task)


@app.get("/api/history")
def history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sentiment: str = Query(default=""),
    product_id: str = Query(default=""),
    start_time: str = Query(default=""),
    end_time: str = Query(default=""),
) -> Dict[str, Any]:
    if sentiment and sentiment not in {"positive", "negative"}:
        raise HTTPException(status_code=400, detail="sentiment 只能是 positive 或 negative")
    return api_response(
        list_history(
            page,
            page_size,
            sentiment=sentiment,
            product_id=product_id,
            start_time=start_time,
            end_time=end_time,
        )
    )


@app.get("/api/statistics/summary")
def statistics_summary(product_id: str = Query(default="")) -> Dict[str, Any]:
    data = summary_statistics(product_id=product_id)
    data["cache"] = prediction_cache.stats()
    return api_response(data)


@app.get("/api/export/{task_id}")
def export_task(task_id: str, file_type: str = Query(default="csv", pattern="^(csv|xlsx)$")) -> StreamingResponse:
    task = get_batch_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="批量任务不存在")
    records = records_by_task(task_id)
    if not records:
        raise HTTPException(status_code=404, detail="该任务没有可导出的记录")

    if file_type == "xlsx":
        output = io.BytesIO()
        pd.DataFrame(records).to_excel(output, index=False)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{task_id}.xlsx"'},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{task_id}.csv"'},
    )
