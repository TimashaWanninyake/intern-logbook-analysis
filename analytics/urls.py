from django.urls import path
from . import views

urlpatterns = [
    path('interns/<int:intern_id>/weekly-report/', views.weekly_intern_report, name='weekly_intern_report'),
]
