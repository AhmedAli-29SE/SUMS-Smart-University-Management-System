from django.contrib import admin
from .models import Enrollment

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course_assignment', 'enrolled_at', 'is_active']
    list_filter = ['is_active', 'course_assignment__semester']
    search_fields = ['student__user__email', 'course_assignment__course__code']
