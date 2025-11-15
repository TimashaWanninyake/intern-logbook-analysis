from __future__ import annotations
from typing import List, Dict, Any
# from collections import Counter


# ON_LEAVE_STATUSES = {"on leave", "leave", "not available", "absent", "sick"}
# WORKING_STATUSES = {"working", "wfh", "remote", "office"}


# def _safe_lower(value: str) -> str:
#     return (value or "").strip().lower()


# def compute_plan_execution_match(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     Yesterday's 'tomorrow_work' vs today's 'todays_work'.
#     Score = ratio of days where there is a reasonable match.
#     """
#     if len(entries) < 2:
#         return {"ratio": 0.0, "score": 0.0}

#     matches = 0
#     comparisons = 0

#     for prev, curr in zip(entries[:-1], entries[1:]):
#         prev_plan = _safe_lower(prev.get("tomorrow_work", ""))
#         today_work = _safe_lower(curr.get("todays_work", ""))

#         if not prev_plan or not today_work:
#             continue

#         comparisons += 1
#         # Very simple heuristic: plan tokens should overlap with today's work
#         overlap = set(prev_plan.split()) & set(today_work.split())
#         if overlap:
#             matches += 1

#     ratio = matches / comparisons if comparisons > 0 else 0.0
#     score = ratio * 100
#     return {"ratio": ratio, "score": score}


# def compute_challenge_resolution(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     For each challenge text, see how many consecutive days it is repeated.
#     Long-running repeated challenges => lower score.
#     """
#     challenge_streaks = []
#     last_challenge = None
#     streak = 0

#     for e in entries:
#         ch = _safe_lower(e.get("challenges", ""))
#         if ch and ch == last_challenge:
#             streak += 1
#         elif ch and ch != last_challenge:
#             if last_challenge is not None:
#                 challenge_streaks.append(streak)
#             last_challenge = ch
#             streak = 1
#         else:
#             if last_challenge is not None:
#                 challenge_streaks.append(streak)
#                 last_challenge = None
#                 streak = 0

#     if last_challenge is not None and streak:
#         challenge_streaks.append(streak)

#     if not challenge_streaks:
#         # No or quickly resolved challenges -> full score
#         return {"avg_streak": 0.0, "score": 100.0}

#     avg_streak = sum(challenge_streaks) / len(challenge_streaks)
#     # Map avg_streak to score (1-day streak -> 100, 7+ days -> ~30)
#     score = max(30.0, 100.0 - (avg_streak - 1) * 10.0)
#     return {"avg_streak": avg_streak, "score": score}


# def compute_continuity(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     Look for repetitive 'todays_work' entries. Too much repetition -> lower score.
#     """
#     works = [_safe_lower(e.get("todays_work", "")) for e in entries if e.get("todays_work")]
#     if not works:
#         return {"repetition_ratio": 0.0, "score": 0.0}

#     counts = Counter(works)
#     most_common_count = counts.most_common(1)[0][1]
#     repetition_ratio = most_common_count / len(works)
#     # If repetition_ratio is 1.0 -> always same => low score.
#     score = max(20.0, 100.0 * (1.0 - repetition_ratio))
#     return {"repetition_ratio": repetition_ratio, "score": score}


# def compute_attendance(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     OnLeave / Not available -> deduct marks.
#     """
#     if not entries:
#         return {"working_days": 0, "leave_days": 0, "score": 0.0}

#     leave_days = 0
#     working_days = 0
#     for e in entries:
#         status = _safe_lower(e.get("status", ""))
#         if any(s in status for s in ON_LEAVE_STATUSES):
#             leave_days += 1
#         elif any(s in status for s in WORKING_STATUSES):
#             working_days += 1

#     total_days = working_days + leave_days
#     attendance_ratio = working_days / total_days if total_days > 0 else 0.0

#     score = attendance_ratio * 100.0  # 100 if no leave, 0 if all leave
#     return {"working_days": working_days, "leave_days": leave_days, "score": score}

# def evaluate_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
#     """
#     High-level scoring pipeline matching the flowchart.
#     """
#     plan_metric = compute_plan_execution_match(entries)
#     challenge_metric = compute_challenge_resolution(entries)
#     continuity_metric = compute_continuity(entries)
#     attendance_metric = compute_attendance(entries)

#     metrics = {
#         "plan_execution": plan_metric,
#         "challenge_resolution": challenge_metric,
#         "continuity": continuity_metric,
#         "attendance": attendance_metric,
#     }

#     overall = compute_overall_score(metrics)

#     return {
#         "metrics": metrics,
#         "overall_score": overall,
#     }

# def compute_overall_score(metrics: Dict[str, Dict[str, Any]]) -> float:
#     """
#     Combine the individual metric scores into one overall score.
#     Weights follow the flowchart:
#       - Plan Execution Match:   30%
#       - Challenge Resolution:   30%
#       - Continuity Check:       20%
#       - Attendance (OnLeave):   20%
#     """
#     plan = metrics["plan_execution"]["score"]
#     challenge = metrics["challenge_resolution"]["score"]
#     continuity = metrics["continuity"]["score"]
#     attendance = metrics["attendance"]["score"]

#     overall = (
#         plan * 0.30 +
#         challenge * 0.30 +
#         continuity * 0.20 +
#         attendance * 0.20
#     )
#     return round(overall, 2)

################################################################################

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

# def calculate_intern_score(insights: dict) -> int:
#     """
#     Simple scoring engine based on extracted insights.
#     """
#     base_score = 50

#     # Score bonus if keywords exist
#     if "keywords" in insights:
#         base_score += len(insights["keywords"]) * 5

#     # Score bonus if sentiment detected
#     if insights.get("sentiment") == "positive":
#         base_score += 10
#     elif insights.get("sentiment") == "negative":
#         base_score -= 10

#     return max(0, min(base_score, 100))  # Clamp between 0–100

