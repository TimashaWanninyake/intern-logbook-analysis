from django.urls import path
from .views import AnalyzeLogbookView

urlpatterns = [
    path('analyze-logbook/', AnalyzeLogbookView.as_view(), name='analyze_logbook'),
]
