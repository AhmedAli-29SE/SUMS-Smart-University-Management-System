from django.contrib import admin
from .models import Department, Course, CourseAssignment


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['is_active']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'credit_hours', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['department', 'is_active']


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'teacher', 'semester', 'year', 'is_active']
    list_filter = ['semester', 'year', 'is_active']
    search_fields = ['course__code', 'teacher__user__email']
