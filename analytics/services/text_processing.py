# lanalytics/services/text_processing.py
import re
import json
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

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

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        output_text = result.get("response", "")
        json_match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            return {"error": "Invalid model response", "raw_output": output_text}

    except Exception as e:
        return {"error": str(e)}
