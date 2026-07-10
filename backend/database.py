"""Database access layer for analysis records and batch tasks."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .settings import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sqlite_conn() -> sqlite3.Connection:
    settings.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_db_path)
    conn.row_factory = sqlite3.Row
    return conn


class MySQLAdapter:
    """Small adapter that gives PyMySQL a sqlite-like `execute` method."""

    def __init__(self, conn: Any):
        self.conn = conn

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor

    def close(self) -> None:
        self.conn.close()


def _mysql_conn() -> Any:
    import pymysql

    conn = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )
    return MySQLAdapter(conn)


@contextmanager
def get_conn() -> Iterable[Any]:
    if settings.database_backend == "mysql":
        conn = _mysql_conn()
    else:
        conn = _sqlite_conn()
    try:
        yield conn
        if settings.database_backend != "mysql":
            conn.commit()
    finally:
        conn.close()


def _placeholder() -> str:
    return "%s" if settings.database_backend == "mysql" else "?"


def _dict(row: Any) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def _normalize_time_bound(value: str, *, end: bool = False) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        return f"{value}T23:59:59+00:00" if end else f"{value}T00:00:00+00:00"
    return value


def _analysis_filters(
    *,
    sentiment: str = "",
    product_id: str = "",
    start_time: str = "",
    end_time: str = "",
) -> tuple[str, List[Any]]:
    ph = _placeholder()
    filters: List[str] = []
    params: List[Any] = []
    if sentiment:
        filters.append(f"sentiment={ph}")
        params.append(sentiment)
    if product_id:
        filters.append(f"product_id={ph}")
        params.append(product_id)
    normalized_start = _normalize_time_bound(start_time)
    normalized_end = _normalize_time_bound(end_time, end=True)
    if normalized_start:
        filters.append(f"created_at>={ph}")
        params.append(normalized_start)
    if normalized_end:
        filters.append(f"created_at<={ph}")
        params.append(normalized_end)
    where = "WHERE " + " AND ".join(filters) if filters else ""
    return where, params


def init_db() -> None:
    """Initialize local SQLite tables.

    MySQL deployments should use `deployment/mysql/init.sql`.
    """

    if settings.database_backend == "mysql":
        return
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                content TEXT NOT NULL,
                clean_content TEXT,
                comment_time TEXT,
                source TEXT DEFAULT 'api',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                comment_id INTEGER,
                product_id TEXT,
                raw_text TEXT NOT NULL,
                clean_text TEXT,
                label INTEGER NOT NULL,
                sentiment TEXT NOT NULL,
                confidence REAL NOT NULL,
                strength REAL NOT NULL,
                cached INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS batch_tasks (
                task_id TEXT PRIMARY KEY,
                filename TEXT,
                status TEXT NOT NULL,
                total INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                avg_strength REAL DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_analysis_records_task_id ON analysis_records(task_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_records_sentiment ON analysis_records(sentiment);
            CREATE INDEX IF NOT EXISTS idx_analysis_records_created_at ON analysis_records(created_at);
            """
        )


def insert_comment(product_id: str, content: str, clean_content: str, comment_time: str = "", source: str = "api") -> int:
    ph = _placeholder()
    now = utc_now()
    with get_conn() as conn:
        cursor = conn.execute(
            f"""
            INSERT INTO comments (product_id, content, clean_content, comment_time, source, created_at)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """,
            (product_id, content, clean_content, comment_time, source, now),
        )
        return int(cursor.lastrowid or 0)


def insert_analysis_record(
    *,
    task_id: str,
    product_id: str,
    raw_text: str,
    clean_text: str,
    label: int,
    sentiment: str,
    confidence: float,
    strength: float,
    cached: bool,
    comment_time: str = "",
) -> Dict[str, Any]:
    ph = _placeholder()
    now = utc_now()
    comment_id = insert_comment(product_id, raw_text, clean_text, comment_time=comment_time)
    with get_conn() as conn:
        cursor = conn.execute(
            f"""
            INSERT INTO analysis_records
            (task_id, comment_id, product_id, raw_text, clean_text, label, sentiment, confidence, strength, cached, created_at)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
            """,
            (
                task_id,
                comment_id,
                product_id,
                raw_text,
                clean_text,
                int(label),
                sentiment,
                float(confidence),
                float(strength),
                1 if cached else 0,
                now,
            ),
        )
        record_id = int(cursor.lastrowid or 0)
    return {
        "id": record_id,
        "task_id": task_id,
        "product_id": product_id,
        "raw_text": raw_text,
        "clean_text": clean_text,
        "label": int(label),
        "sentiment": sentiment,
        "confidence": float(confidence),
        "strength": float(strength),
        "cached": bool(cached),
        "created_at": now,
    }


def create_batch_task(task_id: str, filename: str, total: int) -> None:
    ph = _placeholder()
    with get_conn() as conn:
        conn.execute(
            f"""
            INSERT INTO batch_tasks (task_id, filename, status, total, created_at)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
            """,
            (task_id, filename, "running", total, utc_now()),
        )


def update_batch_task(
    task_id: str,
    *,
    status: str,
    success_count: int,
    failed_count: int,
    positive_count: int,
    negative_count: int,
    avg_strength: float,
    error_message: str = "",
) -> None:
    ph = _placeholder()
    with get_conn() as conn:
        conn.execute(
            f"""
            UPDATE batch_tasks
            SET status={ph}, success_count={ph}, failed_count={ph}, positive_count={ph},
                negative_count={ph}, avg_strength={ph}, error_message={ph}, finished_at={ph}
            WHERE task_id={ph}
            """,
            (
                status,
                success_count,
                failed_count,
                positive_count,
                negative_count,
                avg_strength,
                error_message,
                utc_now(),
                task_id,
            ),
        )


def get_batch_task(task_id: str) -> Optional[Dict[str, Any]]:
    ph = _placeholder()
    with get_conn() as conn:
        row = conn.execute(f"SELECT * FROM batch_tasks WHERE task_id={ph}", (task_id,)).fetchone()
    return _dict(row)


def list_history(
    page: int,
    page_size: int,
    sentiment: str = "",
    product_id: str = "",
    start_time: str = "",
    end_time: str = "",
) -> Dict[str, Any]:
    ph = _placeholder()
    where, params = _analysis_filters(
        sentiment=sentiment,
        product_id=product_id,
        start_time=start_time,
        end_time=end_time,
    )
    offset = (page - 1) * page_size
    with get_conn() as conn:
        total_row = conn.execute(f"SELECT COUNT(*) AS count FROM analysis_records {where}", tuple(params)).fetchone()
        rows = conn.execute(
            f"""
            SELECT * FROM analysis_records
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT {ph} OFFSET {ph}
            """,
            tuple(params + [page_size, offset]),
        ).fetchall()
    return {
        "items": [dict(row) for row in rows],
        "total": int(total_row["count"] if hasattr(total_row, "keys") else total_row[0]),
        "page": page,
        "page_size": page_size,
    }


def summary_statistics(product_id: str = "") -> Dict[str, Any]:
    where, params = _analysis_filters(product_id=product_id)
    with get_conn() as conn:
        row = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) AS negative_count,
                AVG(strength) AS avg_strength
            FROM analysis_records
            {where}
            """,
            tuple(params),
        ).fetchone()
        strength_rows = conn.execute(
            f"""
            SELECT strength
            FROM analysis_records
            {where}
            """,
            tuple(params),
        ).fetchall()
    data = dict(row)
    total = int(data.get("total") or 0)
    positive = int(data.get("positive_count") or 0)
    negative = int(data.get("negative_count") or 0)
    intensity_distribution = [0, 0, 0, 0, 0]
    for item in strength_rows:
        try:
            strength = float(dict(item).get("strength") or 0.0)
        except (TypeError, ValueError):
            strength = 0.0
        index = min(4, max(0, int(strength // 2)))
        intensity_distribution[index] += 1
    return {
        "total": total,
        "positive_count": positive,
        "negative_count": negative,
        "positive_ratio": round(positive / total, 4) if total else 0.0,
        "negative_ratio": round(negative / total, 4) if total else 0.0,
        "avg_strength": round(float(data.get("avg_strength") or 0.0), 2),
        "intensity_distribution": intensity_distribution,
    }


def records_by_task(task_id: str) -> List[Dict[str, Any]]:
    ph = _placeholder()
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT id, task_id, product_id, raw_text, clean_text, label, sentiment,
                   confidence, strength, cached, created_at
            FROM analysis_records
            WHERE task_id={ph}
            ORDER BY id ASC
            """,
            (task_id,),
        ).fetchall()
    return [dict(row) for row in rows]
