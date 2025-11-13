from django.urls import path
from .views import analyze_intern

urlpatterns = [
    path('analyze/', analyze_intern, name='analyze_intern'),
]
