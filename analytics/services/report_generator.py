from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .text_processing import analyze_with_ollama, extract_insights_from_logbook
from .scoring_engine import compute_intern_score, calculate_intern_score
from .utils import fetch_logbook_entries,get_week_range  # adjust if your db module name is different


def _build_log_texts_from_entries(entries: List[Dict[str, Any]]) -> List[str]:
    """
    Turn MongoDB logbook documents into plain text chunks used for scoring & LLM analysis.
    We only use human-readable fields, not ids/dates.
    """
    log_texts: List[str] = []

    for e in entries:
        parts: List[str] = []

        # Today’s work
        if e.get("todays_work"):
            parts.append(str(e["todays_work"]))

        # Challenges
        if e.get("challenges"):
            parts.append(str(e["challenges"]))

        # Tomorrow’s plan (your Mongo field name is `tomorrow_plan`)
        if e.get("tomorrow_plan"):
            parts.append(str(e["tomorrow_plan"]))
        elif e.get("tomorrow_work"):
            # fallback in case old data uses a different key
            parts.append(str(e["tomorrow_work"]))

        text = " ".join(parts).strip()
        if text:
            log_texts.append(text)

    return log_texts


def generate_weekly_report(
    intern_id: str,
    intern_name: str,
    days: int = 7,
) -> Dict[str, Any]:
    """
    Main entry point used by your Django view.
    1. Fetch logbook entries for the given intern and date window.
    2. Compute a numeric score using score_engine.
    3. Call Ollama (gemma3:1b) via analyze_with_ollama to get structured insights.
    4. Return JSON with: intern_id, score, trajectory, milestones_achieved, summary, challenges, recommendations.
    """

    # 1) Get the date window and fetch entries
    start_date, end_date = get_week_range(days=days)
    print("start_date,end_date",start_date,end_date)
    entries = fetch_logbook_entries(intern_id, start_date, end_date)
    print("Entries",entries)

    if not entries:
        # No data → minimal, but still valid JSON in your new format
        return {
            "intern_id": intern_id,
            "score": 0,
            "trajectory": "no-data",
            "milestones_achieved": [],
            "summary": f"No logbook entries found for intern {intern_name} in the given period.",
            "challenges": [],
            "recommendations": [
                "Ask the intern to regularly update their logbook with daily work, challenges, and plans."
            ],
        }

    # 2) Convert entries into raw text snippets
    log_texts = _build_log_texts_from_entries(entries)

    if not log_texts:
        # Entries exist but are empty/low quality
        return {
            "intern_id": intern_id,
            "score": 0,
            "trajectory": "insufficient-data",
            "milestones_achieved": [],
            "summary": f"Logbook entries for intern {intern_name} do not contain enough descriptive information.",
            "challenges": [],
            "recommendations": [
                "Encourage the intern to write more detailed daily updates including what they did, issues faced, and next steps."
            ],
        }

    # 3) Compute numeric score from logs using score_engine.compute_intern_score
    base_score = compute_intern_score(log_texts)

    # 4) Ask Ollama (gemma3:1b) for structured analysis
    ollama_result = analyze_with_ollama(intern_name, log_texts)

    # 4b) Normal path: use Ollama’s JSON, with safe defaults
    trajectory = ollama_result.get("trajectory", "unknown")
    milestones = ollama_result.get("milestones_achieved") or []
    summary = ollama_result.get("summary", "")
    challenges = ollama_result.get("challenges") or []
    recommendations = ollama_result.get("recommendations") or []

    # 5) Final JSON response in the format you requested
    return {
        "intern_id": intern_id,
        "score": base_score,
        "trajectory": trajectory,
        "milestones_achieved": milestones,
        "summary": summary,
        "challenges": challenges,
        "recommendations": recommendations,
    }
