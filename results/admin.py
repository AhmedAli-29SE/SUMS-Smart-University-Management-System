from django.contrib import admin
from .models import Result

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'total', 'grade', 'gpa_points', 'updated_at']
    list_filter = ['grade']
    search_fields = ['enrollment__student__user__email', 'enrollment__course_assignment__course__code']
    readonly_fields = ['total', 'grade', 'gpa_points']
