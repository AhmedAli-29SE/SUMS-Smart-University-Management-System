from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    path('', views.EnrollmentListView.as_view(), name='my_enrollments'),
    path('enroll/', views.EnrollCourseView.as_view(), name='enroll'),
    path('drop/<int:pk>/', views.DropCourseView.as_view(), name='drop'),
    path('all/', views.AdminEnrollmentListView.as_view(), name='admin_list'),
    path('assignment/<int:assignment_pk>/students/', views.EnrolledStudentsView.as_view(), name='enrolled_students'),
]
