from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'date', 'status', 'marked_by']
    list_filter = ['status', 'date']
    search_fields = ['enrollment__student__user__email']
