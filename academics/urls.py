from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Departments
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),

    # Courses
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),

    # Assignments
    path('assignments/', views.CourseAssignmentListView.as_view(), name='assignment_list'),
    path('assignments/create/', views.CourseAssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<int:pk>/', views.CourseAssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:pk>/edit/', views.CourseAssignmentUpdateView.as_view(), name='assignment_update'),
]
