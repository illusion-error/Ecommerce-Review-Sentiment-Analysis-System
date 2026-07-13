"""Text insight utilities for second-stage review analytics.

The backend uses this module to turn stored sentiment records into visible
business insight data: positive/negative word clouds, aspect radar scores and a
rule-based product summary. The implementation intentionally has no mandatory
third-party dependency, so Docker API images can still start quickly.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
STOPWORDS_PATH = RESOURCE_DIR / "stopwords_zh.txt"

DOMAIN_TERMS = {
    "物流",
    "快递",
    "发货",
    "配送",
    "到货",
    "包装",
    "价格",
    "便宜",
    "划算",
    "性价比",
    "优惠",
    "质量",
    "做工",
    "材质",
    "正品",
    "破损",
    "退货",
    "异味",
    "客服",
    "售后",
    "满意",
    "推荐",
    "好用",
    "耐用",
    "失望",
    "垃圾",
    "太贵",
    "发货慢",
    "物流快",
    "质量好",
    "质量差",
}

ASPECT_KEYWORDS = {
    "价格": ["价格", "便宜", "贵", "太贵", "划算", "性价比", "优惠", "值", "不值"],
    "物流": ["物流", "快递", "发货", "配送", "到货", "包装", "速度", "发货慢", "物流快"],
    "质量": ["质量", "做工", "耐用", "正品", "破损", "坏", "材质", "异味", "质量好", "质量差"],
}


def _load_stopwords() -> set[str]:
    default_stopwords = {
        "这个",
        "真的",
        "非常",
        "一个",
        "没有",
        "感觉",
        "还是",
        "就是",
        "比较",
        "东西",
        "商品",
        "已经",
        "但是",
        "然后",
        "因为",
        "所以",
        "可以",
        "不是",
        "有点",
        "一下",
        "我们",
        "你们",
    }
    if not STOPWORDS_PATH.exists():
        return default_stopwords
    words = {
        line.strip()
        for line in STOPWORDS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    return default_stopwords | words


STOPWORDS = _load_stopwords()


def _record_text(record: Dict[str, Any]) -> str:
    return str(record.get("clean_text") or record.get("raw_text") or record.get("content") or "").strip()


def _record_sentiment(record: Dict[str, Any]) -> str:
    sentiment = str(record.get("sentiment") or "").lower()
    if sentiment in {"positive", "negative"}:
        return sentiment
    try:
        return "positive" if int(record.get("label", 1)) == 1 else "negative"
    except (TypeError, ValueError):
        return "positive"


def _jieba_tokens(text: str) -> List[str]:
    try:
        import jieba  # type: ignore

        return [word.strip() for word in jieba.lcut(text) if word.strip()]
    except Exception:
        return []


def _fallback_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for term in DOMAIN_TERMS:
        if term in text:
            tokens.append(term)
    chinese_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    for chunk in chinese_chunks:
        if len(chunk) <= 4:
            tokens.append(chunk)
            continue
        for size in (4, 3, 2):
            for idx in range(0, len(chunk) - size + 1):
                tokens.append(chunk[idx : idx + size])
    english_words = re.findall(r"[A-Za-z]{2,}", text.lower())
    tokens.extend(english_words)
    return tokens


def tokenize(text: str) -> List[str]:
    """Split text into keyword candidates and remove noisy words."""

    if not text:
        return []
    normalized = re.sub(r"\s+", "", text)
    tokens = _jieba_tokens(normalized) or _fallback_tokens(normalized)
    clean_tokens: List[str] = []
    for token in tokens:
        token = token.strip()
        if len(token) < 2:
            continue
        if token in STOPWORDS:
            continue
        if token.isdigit():
            continue
        clean_tokens.append(token)
    return clean_tokens


def _counter_to_items(counter: Counter[str], top_k: int) -> List[Dict[str, Any]]:
    if not counter:
        return []
    max_count = max(counter.values())
    return [
        {"word": word, "count": count, "weight": round(count / max_count, 4)}
        for word, count in counter.most_common(top_k)
    ]


def extract_keywords(records: Iterable[Dict[str, Any]], top_k: int = 30) -> Dict[str, Any]:
    """Return positive and negative Top-K keywords from analyzed records."""

    positive_counter: Counter[str] = Counter()
    negative_counter: Counter[str] = Counter()
    total_records = 0
    for record in records:
        text = _record_text(record)
        if not text:
            continue
        total_records += 1
        target = positive_counter if _record_sentiment(record) == "positive" else negative_counter
        target.update(tokenize(text))
    return {
        "record_count": total_records,
        "positive_words": _counter_to_items(positive_counter, top_k),
        "negative_words": _counter_to_items(negative_counter, top_k),
    }


def score_aspects(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Score price, logistics and quality aspects for radar chart rendering."""

    stats: Dict[str, Dict[str, Any]] = {
        name: {
            "name": name,
            "score": 0.0,
            "total_count": 0,
            "positive_count": 0,
            "negative_count": 0,
            "keywords": [],
            "status": "no_data",
        }
        for name in ASPECT_KEYWORDS
    }
    total_records = 0
    for record in records:
        text = _record_text(record)
        if not text:
            continue
        total_records += 1
        sentiment = _record_sentiment(record)
        for aspect, keywords in ASPECT_KEYWORDS.items():
            matched = [keyword for keyword in keywords if keyword in text]
            if not matched:
                continue
            item = stats[aspect]
            item["total_count"] += 1
            if sentiment == "positive":
                item["positive_count"] += 1
            else:
                item["negative_count"] += 1
            item["keywords"] = sorted(set(item["keywords"]) | set(matched))

    for item in stats.values():
        total = int(item["total_count"])
        if total:
            item["score"] = round(100 * int(item["positive_count"]) / total, 2)
            item["status"] = "ok"
    return {"record_count": total_records, "aspects": list(stats.values())}


def _word_names(items: List[Dict[str, Any]], limit: int = 3) -> List[str]:
    return [str(item.get("word")) for item in items[:limit] if item.get("word")]


def generate_rule_summary(keyword_data: Dict[str, Any], aspect_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a grounded product summary from keyword and aspect evidence."""

    positive_words = _word_names(keyword_data.get("positive_words", []), 3)
    negative_words = _word_names(keyword_data.get("negative_words", []), 3)
    aspects = list(aspect_data.get("aspects", []))
    covered_aspects = [item for item in aspects if int(item.get("total_count") or 0) > 0]

    advantages: List[str] = []
    disadvantages: List[str] = []
    if positive_words:
        advantages.append(f"正向评论中高频出现：{'、'.join(positive_words)}。")
    if negative_words:
        disadvantages.append(f"负向评论中高频出现：{'、'.join(negative_words)}。")

    if covered_aspects:
        best = max(covered_aspects, key=lambda item: float(item.get("score") or 0.0))
        worst = min(covered_aspects, key=lambda item: float(item.get("score") or 0.0))
        advantages.append(f"{best['name']}维度口碑相对较好，评分 {best['score']}。")
        if float(worst.get("score") or 0.0) < 70:
            disadvantages.append(f"{worst['name']}维度仍需关注，评分 {worst['score']}。")
        buying_advice = (
            f"该商品更适合重视{best['name']}体验的用户；"
            f"如果非常关注{worst['name']}，建议结合负向评论进一步判断。"
        )
    else:
        buying_advice = "当前历史评论不足，建议先完成批量分析后再查看购买建议。"

    if not advantages:
        advantages.append("当前正向证据不足，暂不生成明确优点。")
    if not disadvantages:
        disadvantages.append("当前负向证据不足，暂未发现集中槽点。")

    return {
        "mode": "rule_fallback",
        "advantages": advantages,
        "disadvantages": disadvantages,
        "buying_advice": buying_advice,
        "evidence": {
            "positive_words": positive_words,
            "negative_words": negative_words,
            "aspect_scores": {item["name"]: item["score"] for item in aspects},
        },
    }
