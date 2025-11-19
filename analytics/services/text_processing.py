# from __future__ import annotations
# from typing import List, Dict, Any
# from textwrap import shorten
# from datetime import datetime, date


# def normalize_text(value: str) -> str:
#     return " ".join((value or "").split())


# def build_daily_summary(entries: List[Dict[str, Any]]) -> str:
#     """
#     Turn the raw entries into a compact text block for the LLM.
#     """
#     lines = []

#     for e in entries:
#         raw_date = e.get("date")

#         # 1) Handle date types safely
#         if isinstance(raw_date, (datetime, date)):
#             date_str = raw_date.strftime("%Y-%m-%d")
#         elif isinstance(raw_date, str):
#             # assume it's already like "2025-08-24"
#             date_str = raw_date
#         else:
#             date_str = "unknown-date"

#         # 2) Normalize the rest of the fields
#         status = normalize_text(e.get("status", ""))
#         stack = normalize_text(e.get("tech_stack", ""))
#         today = normalize_text(e.get("todays_work", ""))
#         challenges = normalize_text(e.get("challenges", ""))

#         # 🔧 IMPORTANT: your Mongo field is `tomorrow_plan`, not `tomorrow_work`
#         tomorrow = normalize_text(
#             e.get("tomorrow_plan") or e.get("tomorrow_work", "")
#         )

#         line = (
#             f"Date: {date_str}\n"
#             f"  Status: {status}\n"
#             f"  Tech stack: {stack}\n"
#             f"  Today's work: {today}\n"
#             f"  Challenges: {challenges}\n"
#             f"  Tomorrow's plan: {tomorrow}\n"
#         )
#         lines.append(line)

#     return "\n".join(lines)


# def truncate_for_prompt(text: str, max_chars: int = 12000) -> str:
#     """
#     Protect the LLM from overly long prompts.
#     """
#     if len(text) <= max_chars:
#         return text
#     return shorten(text, width=max_chars, placeholder=" ... [TRUNCATED]")

import re
import json
from django.conf import settings
import requests

OLLAMA_API_URL = getattr(settings, "OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = getattr(settings, "OLLAMA_MODEL", "gemma3:1b")


def clean_text(text: str) -> str:
    """Remove unnecessary symbols and extra spaces."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^A-Za-z0-9.,;:!?()\-\n ]', '', text)
    return text.strip()


def build_analysis_prompt(intern_name: str, log_text: str) -> str:
    """Create structured prompt for Ollama model."""
    return f"""
You are an AI system analyzing intern daily logbook entries.

Intern Name: {intern_name}

Each entry describes daily work, challenges, and future plans.
Your tasks:
1. Summarize what the intern accomplished.
2. Identify key milestones or achievements.
3. Detect challenges or blockers.
4. Evaluate trajectory (improving / stagnant / declining).
5. Suggest personalized recommendations.

Return **strictly JSON output** as:
{{
  "trajectory": "<string>",
  "milestones_achieved": ["<string>", "..."],
  "summary": "<short paragraph>",
  "challenges": ["<string>", "..."],
  "recommendations": ["<string>", "..."]
}}

Logbook entries:
---
{log_text}
---
"""
def extract_insights_from_logbook(log_text: str) -> dict:
    if not log_text or len(log_text.strip()) == 0:
        return {"error": "Empty log text"}

    insights = {
        "cleaned_text": log_text.strip(),
        "sentiment": "positive",
        "keywords": ["task", "completed", "progress"],
        "summary": f"User worked on tasks: {log_text[:50]}..."
    }
    return insights


def analyze_with_ollama(intern_name: str, log_entries: list[str]) -> dict:
    """Send cleaned text to Ollama (gemma3:1b) and return structured JSON response."""
    log_text = "\n".join(clean_text(entry) for entry in log_entries)
    prompt = build_analysis_prompt(intern_name, log_text)
    url = OLLAMA_API_URL.rstrip("/") + "/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_k": 50,
            "top_p": 0.95
  }
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # print("\nOLLAMA RAW RESPONSE:", response.text)

        result = response.json()
        output_text = result.get("response", "")

        print("\nOLLAMA response field:", output_text)
        
        json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"error": "Invalid model response", "raw_output": output_text}

    except Exception as e:
        return {"error": str(e)}