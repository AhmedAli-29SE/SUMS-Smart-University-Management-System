from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView

from accounts.mixins import TeacherRequiredMixin, StudentRequiredMixin, AdminOrTeacherMixin
from academics.models import CourseAssignment
from enrollment.models import Enrollment
from .forms import ResultForm
from .models import Result


class EnterResultsView(TeacherRequiredMixin, View):
    """Teacher selects a course to enter results."""
    template_name = 'results/select_course.html'

    def get(self, request):
        assignments = CourseAssignment.objects.filter(
            teacher=request.user.teacher_profile,
            is_active=True
        ).select_related('course')
        return render(request, self.template_name, {'assignments': assignments})


class CourseResultListView(TeacherRequiredMixin, View):
    """Teacher views/enters marks for all students in a course."""
    template_name = 'results/course_results.html'

    def get_assignment(self, pk, teacher_profile):
        return get_object_or_404(
            CourseAssignment, pk=pk, teacher=teacher_profile
        )

    def get(self, request, assignment_pk):
        assignment = self.get_assignment(assignment_pk, request.user.teacher_profile)
        enrollments = Enrollment.objects.filter(
            course_assignment=assignment,
            is_active=True
        ).select_related('student__user').prefetch_related('result')

        result_data = []
        for e in enrollments:
            result = getattr(e, 'result', None)
            form = ResultForm(instance=result, prefix=str(e.pk))
            result_data.append({'enrollment': e, 'result': result, 'form': form})

        return render(request, self.template_name, {
            'assignment': assignment,
            'result_data': result_data,
        })

    def post(self, request, assignment_pk):
        assignment = self.get_assignment(assignment_pk, request.user.teacher_profile)
        enrollments = Enrollment.objects.filter(
            course_assignment=assignment,
            is_active=True
        ).select_related('student__user')

        all_valid = True
        result_data = []

        for e in enrollments:
            result = getattr(e, 'result', None)
            form = ResultForm(request.POST, instance=result, prefix=str(e.pk))
            if form.is_valid():
                r = form.save(commit=False)
                r.enrollment = e
                r.entered_by = request.user
                r.save()  # triggers auto grade/gpa calculation
            else:
                all_valid = False
            result_data.append({'enrollment': e, 'result': result, 'form': form})

        if all_valid:
            messages.success(request, 'Results saved successfully.')
            return redirect('results:course_results', assignment_pk=assignment_pk)

        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'assignment': assignment,
            'result_data': result_data,
        })


class EnterSingleResultView(TeacherRequiredMixin, View):
    """Enter/update result for one specific enrollment."""
    template_name = 'results/single_result_form.html'

    def get_enrollment(self, pk, teacher_profile):
        return get_object_or_404(
            Enrollment,
            pk=pk,
            course_assignment__teacher=teacher_profile
        )

    def get(self, request, enrollment_pk):
        enrollment = self.get_enrollment(enrollment_pk, request.user.teacher_profile)
        result = getattr(enrollment, 'result', None)
        form = ResultForm(instance=result)
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'result': result,
            'form': form,
        })

    def post(self, request, enrollment_pk):
        enrollment = self.get_enrollment(enrollment_pk, request.user.teacher_profile)
        result = getattr(enrollment, 'result', None)
        form = ResultForm(request.POST, instance=result)
        if form.is_valid():
            r = form.save(commit=False)
            r.enrollment = enrollment
            r.entered_by = request.user
            r.save()
            messages.success(request, 'Result saved.')
            return redirect(
                'results:course_results',
                assignment_pk=enrollment.course_assignment_id
            )
        return render(request, self.template_name, {
            'enrollment': enrollment,
            'form': form,
        })


class StudentResultsView(StudentRequiredMixin, View):
    """Student views their own results across all courses."""
    template_name = 'results/student_results.html'

    def get(self, request):
        profile = request.user.student_profile
        results = Result.objects.filter(
            enrollment__student=profile
        ).select_related(
            'enrollment__course_assignment__course',
            'enrollment__course_assignment__teacher__user',
        ).order_by(
            '-enrollment__course_assignment__year',
            'enrollment__course_assignment__semester'
        )

        # Group by semester/year
        semesters = {}
        for r in results:
            ca = r.enrollment.course_assignment
            key = (ca.year, ca.semester)
            if key not in semesters:
                semesters[key] = {
                    'year': ca.year,
                    'semester': ca.semester,
                    'results': [],
                    'gpa': None,
                }
            semesters[key]['results'].append(r)

        # Calculate per-semester GPA
        for key, sem_data in semesters.items():
            year, semester = key
            sem_data['gpa'] = Result.get_semester_gpa(profile, semester, year)

        cgpa = Result.get_cgpa(profile)

        return render(request, self.template_name, {
            'semesters': sorted(semesters.values(), key=lambda x: (-x['year'], x['semester'])),
            'cgpa': cgpa,
            'profile': profile,
        })


class ResultTranscriptView(StudentRequiredMixin, View):
    """Printable transcript view for the student."""
    template_name = 'results/transcript.html'

    def get(self, request):
        profile = request.user.student_profile
        results = Result.objects.filter(
            enrollment__student=profile
        ).select_related(
            'enrollment__course_assignment__course',
            'enrollment__course_assignment__teacher__user',
        ).order_by(
            'enrollment__course_assignment__year',
            'enrollment__course_assignment__semester',
            'enrollment__course_assignment__course__code',
        )

        semesters = {}
        for r in results:
            ca = r.enrollment.course_assignment
            key = (ca.year, ca.semester)
            if key not in semesters:
                semesters[key] = {'year': ca.year, 'semester': ca.semester, 'results': []}
            semesters[key]['results'].append(r)

        for key, sem_data in semesters.items():
            year, semester = key
            sem_data['gpa'] = Result.get_semester_gpa(profile, semester, year)

        return render(request, self.template_name, {
            'profile': profile,
            'semesters': sorted(semesters.values(), key=lambda x: (x['year'], x['semester'])),
            'cgpa': Result.get_cgpa(profile),
        })


class AdminResultsView(AdminOrTeacherMixin, ListView):
    """Admin/teacher overview of all results."""
    model = Result
    template_name = 'results/admin_results.html'
    context_object_name = 'results'
    paginate_by = 25

    def get_queryset(self):
        qs = Result.objects.select_related(
            'enrollment__student__user',
            'enrollment__course_assignment__course',
            'enrollment__course_assignment__teacher__user',
        ).order_by('-updated_at')

        if self.request.user.is_teacher:
            qs = qs.filter(
                enrollment__course_assignment__teacher=self.request.user.teacher_profile
            )
        return qs
