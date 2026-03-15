from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView

from accounts.mixins import StudentRequiredMixin, AdminRequiredMixin, AdminOrTeacherMixin
from .forms import EnrollmentForm
from .models import Enrollment


class EnrollmentListView(StudentRequiredMixin, ListView):
    """Student views their own enrolled courses."""
    template_name = 'enrollment/my_enrollments.html'
    context_object_name = 'enrollments'
    paginate_by = 20

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user.student_profile
        ).select_related(
            'course_assignment__course__department',
            'course_assignment__teacher__user',
        ).order_by('-enrolled_at')


class EnrollCourseView(StudentRequiredMixin, View):
    template_name = 'enrollment/enroll.html'

    def get(self, request):
        profile = request.user.student_profile
        form = EnrollmentForm(student_profile=profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        profile = request.user.student_profile
        form = EnrollmentForm(student_profile=profile, data=request.POST)
        if form.is_valid():
            ca = form.cleaned_data['course_assignment']
            try:
                enrollment = Enrollment.objects.create(
                    student=profile,
                    course_assignment=ca
                )
                messages.success(
                    request,
                    f'Successfully enrolled in {ca.course.name}!'
                )
                return redirect('enrollment:my_enrollments')
            except IntegrityError:
                messages.error(request, 'You are already enrolled in this course.')
        return render(request, self.template_name, {'form': form})


class DropCourseView(StudentRequiredMixin, View):
    def post(self, request, pk):
        enrollment = get_object_or_404(
            Enrollment,
            pk=pk,
            student=request.user.student_profile
        )
        course_name = enrollment.course_assignment.course.name
        enrollment.delete()
        messages.success(request, f'Dropped {course_name} successfully.')
        return redirect('enrollment:my_enrollments')


class AdminEnrollmentListView(AdminOrTeacherMixin, ListView):
    """Admin/Teacher view of all enrollments, filterable."""
    model = Enrollment
    template_name = 'enrollment/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 25

    def get_queryset(self):
        qs = Enrollment.objects.select_related(
            'student__user',
            'course_assignment__course',
            'course_assignment__teacher__user',
        ).order_by('-enrolled_at')

        # Teachers only see their own course enrollments
        if self.request.user.is_teacher:
            qs = qs.filter(course_assignment__teacher=self.request.user.teacher_profile)

        course = self.request.GET.get('course')
        semester = self.request.GET.get('semester')
        if course:
            qs = qs.filter(course_assignment__course_id=course)
        if semester:
            qs = qs.filter(course_assignment__semester=semester)
        return qs


class EnrolledStudentsView(AdminOrTeacherMixin, View):
    """View enrolled students for a specific course assignment."""
    template_name = 'enrollment/enrolled_students.html'

    def get(self, request, assignment_pk):
        from academics.models import CourseAssignment
        assignment = get_object_or_404(CourseAssignment, pk=assignment_pk)

        # Teacher can only see their own assignments
        if request.user.is_teacher and assignment.teacher != request.user.teacher_profile:
            messages.error(request, 'Access denied.')
            return redirect('enrollment:admin_list')

        enrollments = Enrollment.objects.filter(
            course_assignment=assignment
        ).select_related('student__user', 'student__department')

        return render(request, self.template_name, {
            'assignment': assignment,
            'enrollments': enrollments,
        })
