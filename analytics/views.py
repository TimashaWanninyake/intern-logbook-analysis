from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from analytics.services.text_processing import extract_insights_from_logbook
from analytics.services.scoring_engine import calculate_intern_score
from analytics.services.report_generator import generate_project_report


class AnalyzeLogbookView(APIView):

    def post(self, request):
        try:
            log_data = request.data.get("log_data")

            if not log_data:
                return Response({"error": "No log data provided."}, status=400)

            insights = extract_insights_from_logbook(log_data)
            score = calculate_intern_score(insights)
            report = generate_project_report(
                insights=insights,
                score=score,
                intern_name="Dilmi Madumalka"
            )

            return Response(report, status=200)

        except Exception as e:
            return Response(
                {"error": str(e), "type": "SERVER_ERROR"},
                status=500,
                content_type="application/json"
            )
