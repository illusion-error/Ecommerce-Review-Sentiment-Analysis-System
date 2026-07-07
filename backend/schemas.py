"""Pydantic request and response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Any = None
    code: int = 0


class SingleSentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Review text to analyze")
    product_id: Optional[str] = Field(default="", description="Optional product or category id")
    comment_time: Optional[str] = Field(default="", description="Optional review time")


class SentimentResult(BaseModel):
    text: str
    clean_text: str
    label: int
    sentiment: str
    confidence: float
    strength: float
    cached: bool = False


class BatchSummary(BaseModel):
    task_id: str
    total: int
    success_count: int
    failed_count: int
    positive_count: int
    negative_count: int
    avg_strength: float
    results: List[Dict[str, Any]]

