from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('mark/', views.MarkAttendanceSelectView.as_view(), name='mark_select'),
    path('mark/<int:assignment_pk>/', views.MarkAttendanceView.as_view(), name='mark'),
    path('report/<int:assignment_pk>/', views.AttendanceReportView.as_view(), name='report'),
    path('my/', views.StudentAttendanceView.as_view(), name='my_attendance'),
    path('my/<int:enrollment_pk>/', views.AttendanceDetailView.as_view(), name='course_detail'),
]
