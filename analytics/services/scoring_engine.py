from __future__ import annotations
from typing import List, Dict, Any
from textblob import TextBlob
import statistics

def sentiment_score(text: str) -> float:
    """Simple polarity-based sentiment scoring."""
    blob = TextBlob(text)
    polarity = (blob.sentiment.polarity + 1) / 2
    return round(polarity * 100, 2)


def consistency_score(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Check how consistent the intern is based on log entry lengths."""
    lengths = [len(entry.split()) for entry in log_entries if entry.strip()]
    if not lengths:
        return 0.0
    avg_len = statistics.mean(lengths)
    std_dev = statistics.pstdev(lengths)
    score = max(0.0, 1.0 - (std_dev / (avg_len + 1e-5))) * 100
    return round(score, 2)


def effort_score(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Keyword-based effort detection."""
    keywords = ["completed", "developed", "tested", "debugged", "implemented", "fixed", "optimized"]
    hits = sum(entry.lower().count(kw) for entry in log_entries for kw in keywords)
    total_words = sum(len(entry.split()) for entry in log_entries)
    if total_words == 0:
        return 0.0
    return round((hits / total_words) * 100, 2)


def compute_intern_score(log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Weighted scoring system combining all metrics."""
    combined_text = " ".join(log_entries)
    sentiment = sentiment_score(combined_text)
    consistency = consistency_score(log_entries)
    effort = effort_score(log_entries)

    print()

    final = (sentiment * 0.3) + (consistency * 0.3) + (effort * 0.4)
    return int(round(final, 0))

def calculate_intern_score(insights: dict) -> int:
    """
    Simple scoring engine based on extracted insights.
    """
    base_score = 50

    # Score bonus if keywords exist
    if "keywords" in insights:
        base_score += len(insights["keywords"]) * 5

    # Score bonus if sentiment detected
    if insights.get("sentiment") == "positive":
        base_score += 10
    elif insights.get("sentiment") == "negative":
        base_score -= 10

    return max(0, min(base_score, 100))  # Clamp between 0–100

