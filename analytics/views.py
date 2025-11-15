from __future__ import annotations
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services.report_generator import generate_weekly_report


@require_GET
def weekly_intern_report(request, intern_id: str):

    try:
        intern_id = int(intern_id)
    except (TypeError, ValueError):
        return JsonResponse(
            {
                "error": "Invalid intern_id in URL. It must be an integer.",
                "internIdRaw": intern_id,
            },
            status=400,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )

    
    intern_name = request.GET.get("name", f"Intern {intern_id}")
    try:
        days = int(request.GET.get("days", "7"))
    except ValueError:
        days = 7

    report = generate_weekly_report(
        intern_id=intern_id,
        intern_name=intern_name,
        days=days,
    )

    return JsonResponse(report, safe=False, json_dumps_params={"ensure_ascii": False, "indent": 2})
