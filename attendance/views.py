from datetime import date as date_type
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView

from accounts.mixins import TeacherRequiredMixin, StudentRequiredMixin, AdminOrTeacherMixin
from academics.models import CourseAssignment
from enrollment.models import Enrollment
from .forms import AttendanceDateForm, BulkAttendanceForm
from .models import Attendance


class MarkAttendanceSelectView(TeacherRequiredMixin, View):
    """Step 1: Teacher selects which course assignment and date."""
    template_name = 'attendance/select_course.html'

    def get(self, request):
        assignments = CourseAssignment.objects.filter(
            teacher=request.user.teacher_profile,
            is_active=True
        ).select_related('course')
        return render(request, self.template_name, {
            'assignments': assignments,
            'date_form': AttendanceDateForm(),
        })


class MarkAttendanceView(TeacherRequiredMixin, View):
    """Step 2: Teacher marks attendance for all enrolled students."""
    template_name = 'attendance/mark_attendance.html'

    def get_assignment(self, pk, teacher_profile):
        return get_object_or_404(
            CourseAssignment,
            pk=pk,
            teacher=teacher_profile,
            is_active=True
        )

    def get(self, request, assignment_pk):
        assignment = self.get_assignment(assignment_pk, request.user.teacher_profile)
        date_str = request.GET.get('date', str(date_type.today()))
        try:
            selected_date = date_type.fromisoformat(date_str)
        except ValueError:
            selected_date = date_type.today()

        enrollments = Enrollment.objects.filter(
            course_assignment=assignment,
            is_active=True
        ).select_related('student__user')

        form = BulkAttendanceForm(enrollments=enrollments, date=selected_date)
        return render(request, self.template_name, {
            'assignment': assignment,
            'selected_date': selected_date,
            'form': form,
            'enrollments': enrollments,
        })

    def post(self, request, assignment_pk):
        assignment = self.get_assignment(assignment_pk, request.user.teacher_profile)
        date_str = request.POST.get('date', str(date_type.today()))
        try:
            selected_date = date_type.fromisoformat(date_str)
        except ValueError:
            selected_date = date_type.today()

        enrollments = Enrollment.objects.filter(
            course_assignment=assignment,
            is_active=True
        ).select_related('student__user')

        form = BulkAttendanceForm(enrollments=enrollments, date=selected_date, data=request.POST)

        if form.is_valid():
            with transaction.atomic():
                for enrollment in enrollments:
                    status = form.cleaned_data[f'status_{enrollment.pk}']
                    remarks = form.cleaned_data.get(f'remarks_{enrollment.pk}', '')
                    Attendance.objects.update_or_create(
                        enrollment=enrollment,
                        date=selected_date,
                        defaults={
                            'status': status,
                            'remarks': remarks,
                            'marked_by': request.user,
                        }
                    )
            messages.success(
                request,
                f'Attendance marked for {selected_date} ({enrollments.count()} students).'
            )
            return redirect('attendance:mark_select')

        return render(request, self.template_name, {
            'assignment': assignment,
            'selected_date': selected_date,
            'form': form,
            'enrollments': enrollments,
        })


class AttendanceReportView(AdminOrTeacherMixin, View):
    """Per-course attendance report for teacher/admin."""
    template_name = 'attendance/report.html'

    def get(self, request, assignment_pk):
        assignment = get_object_or_404(CourseAssignment, pk=assignment_pk)

        # Teacher guard
        if request.user.is_teacher and assignment.teacher != request.user.teacher_profile:
            messages.error(request, 'Access denied.')
            return redirect('attendance:mark_select')

        enrollments = Enrollment.objects.filter(
            course_assignment=assignment
        ).select_related('student__user').prefetch_related('attendance_records')

        report = []
        all_dates = sorted(set(
            Attendance.objects.filter(
                enrollment__course_assignment=assignment
            ).values_list('date', flat=True)
        ))

        for e in enrollments:
            records_by_date = {a.date: a for a in e.attendance_records.all()}
            row = {
                'student': e.student,
                'records': [records_by_date.get(d) for d in all_dates],
                'percentage': e.get_attendance_percentage(),
            }
            report.append(row)

        return render(request, self.template_name, {
            'assignment': assignment,
            'dates': all_dates,
            'report': report,
        })


class StudentAttendanceView(StudentRequiredMixin, View):
    """Student's own attendance view."""
    template_name = 'attendance/student_attendance.html'

    def get(self, request):
        profile = request.user.student_profile
        summary = Attendance.get_student_summary(profile)
        return render(request, self.template_name, {
            'summary': summary,
            'profile': profile,
        })


class AttendanceDetailView(StudentRequiredMixin, View):
    """Student drills into a single course attendance."""
    template_name = 'attendance/course_detail.html'

    def get(self, request, enrollment_pk):
        enrollment = get_object_or_404(
            Enrollment,
            pk=enrollment_pk,
            student=request.user.student_profile
        )
        records = enrollment.attendance_records.all().order_by('date')
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'records': records,
            'percentage': enrollment.get_attendance_percentage(),
        })
