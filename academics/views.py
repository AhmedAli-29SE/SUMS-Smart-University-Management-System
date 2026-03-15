from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView

from accounts.mixins import AdminRequiredMixin, AdminOrTeacherMixin
from .forms import DepartmentForm, CourseForm, CourseAssignmentForm
from .models import Department, Course, CourseAssignment


# ── Departments ────────────────────────────────────────────────

class DepartmentListView(AdminOrTeacherMixin, ListView):
    model = Department
    template_name = 'academics/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        return Department.objects.prefetch_related('courses', 'students', 'teachers').order_by('name')


class DepartmentCreateView(AdminRequiredMixin, View):
    template_name = 'academics/department_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': DepartmentForm(), 'action': 'Create'})

    def post(self, request):
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f'Department "{dept.name}" created successfully.')
            return redirect('academics:department_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class DepartmentUpdateView(AdminRequiredMixin, View):
    template_name = 'academics/department_form.html'

    def get(self, request, pk):
        dept = get_object_or_404(Department, pk=pk)
        return render(request, self.template_name, {'form': DepartmentForm(instance=dept), 'action': 'Update', 'object': dept})

    def post(self, request, pk):
        dept = get_object_or_404(Department, pk=pk)
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('academics:department_list')
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'object': dept})


class DepartmentDetailView(AdminOrTeacherMixin, DetailView):
    model = Department
    template_name = 'academics/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dept = self.get_object()
        ctx['courses'] = dept.courses.filter(is_active=True).select_related('department')
        ctx['teachers'] = dept.teachers.select_related('user')
        ctx['students'] = dept.students.select_related('user').order_by('semester')[:10]
        return ctx


# ── Courses ────────────────────────────────────────────────────

class CourseListView(AdminOrTeacherMixin, ListView):
    model = Course
    template_name = 'academics/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        qs = Course.objects.select_related('department').order_by('code')
        dept = self.request.GET.get('department')
        search = self.request.GET.get('search', '').strip()
        if dept:
            qs = qs.filter(department_id=dept)
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(code__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['departments'] = Department.objects.filter(is_active=True)
        ctx['selected_dept'] = self.request.GET.get('department', '')
        ctx['search'] = self.request.GET.get('search', '')
        return ctx


class CourseCreateView(AdminRequiredMixin, View):
    template_name = 'academics/course_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': CourseForm(), 'action': 'Create'})

    def post(self, request):
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" created successfully.')
            return redirect('academics:course_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class CourseUpdateView(AdminRequiredMixin, View):
    template_name = 'academics/course_form.html'

    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        return render(request, self.template_name, {'form': CourseForm(instance=course), 'action': 'Update', 'object': course})

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('academics:course_list')
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'object': course})


# ── Course Assignments ─────────────────────────────────────────

class CourseAssignmentListView(AdminOrTeacherMixin, ListView):
    model = CourseAssignment
    template_name = 'academics/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        qs = CourseAssignment.objects.select_related(
            'course__department', 'teacher__user', 'teacher__department'
        ).order_by('-year', 'semester')

        user = self.request.user
        if user.is_teacher:
            qs = qs.filter(teacher=user.teacher_profile)

        semester = self.request.GET.get('semester')
        year = self.request.GET.get('year')
        if semester:
            qs = qs.filter(semester=semester)
        if year:
            qs = qs.filter(year=year)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['semesters'] = CourseAssignment.Semester.choices
        ctx['selected_semester'] = self.request.GET.get('semester', '')
        ctx['selected_year'] = self.request.GET.get('year', '')
        return ctx


class CourseAssignmentCreateView(AdminRequiredMixin, View):
    template_name = 'academics/assignment_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': CourseAssignmentForm(), 'action': 'Create'})

    def post(self, request):
        form = CourseAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Course assignment created: {assignment}')
            return redirect('academics:assignment_list')
        return render(request, self.template_name, {'form': form, 'action': 'Create'})


class CourseAssignmentUpdateView(AdminRequiredMixin, View):
    template_name = 'academics/assignment_form.html'

    def get(self, request, pk):
        obj = get_object_or_404(CourseAssignment, pk=pk)
        return render(request, self.template_name, {'form': CourseAssignmentForm(instance=obj), 'action': 'Update', 'object': obj})

    def post(self, request, pk):
        obj = get_object_or_404(CourseAssignment, pk=pk)
        form = CourseAssignmentForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully.')
            return redirect('academics:assignment_list')
        return render(request, self.template_name, {'form': form, 'action': 'Update', 'object': obj})


class CourseAssignmentDetailView(AdminOrTeacherMixin, DetailView):
    model = CourseAssignment
    template_name = 'academics/assignment_detail.html'
    context_object_name = 'assignment'

    def get_queryset(self):
        return CourseAssignment.objects.select_related(
            'course__department', 'teacher__user'
        ).prefetch_related('enrollments__student__user')
