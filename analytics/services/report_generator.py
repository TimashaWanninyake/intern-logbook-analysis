from __future__ import annotations
# import json
# from typing import Dict, Any
# import requests
# from django.conf import settings
# from .utils import fetch_logbook_entries, get_week_range
# from .text_processing import build_daily_summary, truncate_for_prompt
# from .scoring_engine import evaluate_entries
# from datetime import datetime


# def call_ollama(prompt: str) -> Dict[str, Any]:
#     """
#     Call Ollama's local LLM and expect a JSON string in the 'response' field.
#     """
#     base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
#     model = getattr(settings, "OLLAMA_MODEL", "gemma3:1b")

#     url = base_url.rstrip("/") + "/api/generate"
#     payload = {
#         "model": model,
#         "prompt": prompt,
#         "stream": False,
#     }

#     resp = requests.post(url, json=payload, timeout=120)
#     resp.raise_for_status()
#     data = resp.json()
#     raw_text = data.get("response", "").strip()

#     # The model is instructed to respond with JSON.
#     try:
#         return json.loads(raw_text)
#     except json.JSONDecodeError:
#         # Fallback: wrap raw text
#         return {"raw_llm_output": raw_text}


# def build_llm_prompt(
#     intern_name: str,
#     entries_summary: str,
#     scoring: Dict[str, Any],
# ) -> str:
#     """
#     Build the instruction for Ollama.
#     """
#     metrics = scoring["metrics"]
#     overall_score = scoring["overall_score"]

#     prompt = f"""
# You are an internship supervisor analysing an intern's weekly logbook.

# You must STRICTLY reply with a single valid JSON object only.
# Do NOT include any explanation or text outside the JSON.

# JSON schema:
# {{
#   "internName": string,
#   "overallScore": number,          // 0-100, can start from provided score but you may adjust slightly
#   "keyHighlights": [string],       // 3-7 bullet points
#   "risksAndBlockers": [string],    // specific issues or risks
#   "recommendedActions": [string],  // clear action items for intern and supervisor
#   "scoreBreakdown": {{
#     "planExecutionMatch": number,  // 0-100
#     "challengeResolution": number,
#     "continuity": number,
#     "attendance": number
#   }}
# }}

# Base your reasoning on:

# 1) RULE-BASED SCORES FROM ANALYTICS ENGINE
# - Plan–Execution Match score: {metrics["plan_execution"]["score"]:.2f}
# - Challenge Resolution score: {metrics["challenge_resolution"]["score"]:.2f}
# - Continuity score: {metrics["continuity"]["score"]:.2f}
# - Attendance score: {metrics["attendance"]["score"]:.2f}
# - Overall base score: {overall_score:.2f}

# 2) WEEKLY LOGBOOK SUMMARY
# {entries_summary}

# Guidelines:
# - Higher score if plans match execution, challenges are resolved within few days, work is continuous and non-repetitive, and attendance is good.
# - Lower score if plans are ignored, challenges persist, entries are copy-pasted, or the intern is frequently on leave.
# - Use concise, professional language in bullets.
# - Use numbers (0-100) for all scores.

# Now generate the JSON.
# """
#     return truncate_for_prompt(prompt)


# def generate_weekly_report(
#     intern_id: str,
#     intern_name: str,
#     days: int = 7,
# ) -> Dict[str, Any]:
#     """
#     Main entry point used by the Django view.
#     Returns a JSON-serializable dict.
#     """
#     start_date, end_date = get_week_range(days=days)
#     print("sd", type(start_date),end_date)
#     entries = fetch_logbook_entries(intern_id, start_date, end_date)
#     print("Entries",entries)
#     if not entries:
#         return {
#             "internId": intern_id,
#             "internName": intern_name,
#             "hasData": False,
#             "message": "No logbook entries found for the given week.",
#         }

#     scoring = evaluate_entries(entries)
#     summary = build_daily_summary(entries)
#     prompt = build_llm_prompt(intern_name, summary, scoring)

#     llm_json = call_ollama(prompt)

#     # Attach some raw metrics for transparency.
#     report: Dict[str, Any] = {
#         "internId": intern_id,
#         "internName": intern_name,
#         "hasData": True,
#         "analytics": scoring,
#         "llmReport": llm_json,
#     }
#     return report

# analytics/services/report_generator.py

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
    intern_id: int,
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
    entries = fetch_logbook_entries(intern_id, start_date, end_date)
    print("Entries",entries)
    entries = fetch_logbook_entries(intern_id, start_date, end_date)

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
