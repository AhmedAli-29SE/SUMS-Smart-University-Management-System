from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('enter/', views.EnterResultsView.as_view(), name='enter'),
    path('enter/<int:assignment_pk>/', views.CourseResultListView.as_view(), name='course_results'),
    path('enter/enrollment/<int:enrollment_pk>/', views.EnterSingleResultView.as_view(), name='single_result'),
    path('my/', views.StudentResultsView.as_view(), name='my_results'),
    path('transcript/', views.ResultTranscriptView.as_view(), name='transcript'),
    path('all/', views.AdminResultsView.as_view(), name='admin_results'),
]
