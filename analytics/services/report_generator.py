# log_analysis/services/report_generator.py
from datetime import datetime
from .text_processing import analyze_with_ollama
from .scoring_engine import compute_intern_score

def generate_project_report(intern_logs: list[dict]) -> dict:
    """
    Generate final project report JSON from intern log data.
    Each intern_log dict contains: { 'intern_id', 'name', 'logs': [ ... ] }
    """
    all_intern_reports = []
    milestones = []
    improving_count = 0

    for intern in intern_logs:
        name = intern.get("name")
        logs = intern.get("logs", [])
        intern_id = intern.get("intern_id")

        # AI analysis
        ai_result = analyze_with_ollama(name, logs)
        if "error" in ai_result:
            ai_result = {
                "trajectory": "unknown",
                "milestones_achieved": [],
                "recommendations": ["AI analysis failed"]
            }

        # Scoring
        score = compute_intern_score(logs, ai_result)

        if ai_result.get("trajectory", "").lower() == "improving":
            improving_count += 1

        milestones.extend(ai_result.get("milestones_achieved", []))

        all_intern_reports.append({
            "intern_id": intern_id,
            "name": name,
            "score": score,
            "drivers": ai_result.get("challenges", []),
            "recommendations": ai_result.get("recommendations", [])
        })

    # Determine project-wide summary trajectory
    if not intern_logs:
        trajectory = "unknown"
    elif improving_count >= len(intern_logs) * 0.6:
        trajectory = "improving"
    elif improving_count >= len(intern_logs) * 0.3:
        trajectory = "stable"
    else:
        trajectory = "declining"

    final_report = {
        "project_summary": {
            "trajectory": trajectory,
            "milestones_achieved": list(set(milestones))
        },
        "interns": all_intern_reports,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    return final_report
