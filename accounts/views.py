import logging
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView

from .forms import UserCreateForm, UserUpdateForm, StudentProfileForm, TeacherProfileForm, ChangePasswordForm
from .mixins import AdminRequiredMixin
from .models import CustomUser, StudentProfile, TeacherProfile

logger = logging.getLogger('smart_university')


class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, 'home.html')


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            return render(request, self.template_name, {
                'error': 'Please enter both email and password.',
                'email_value': email,
            })

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                next_url = request.GET.get('next')
                return redirect(next_url) if next_url else redirect('accounts:dashboard')
            else:
                return render(request, self.template_name, {
                    'error': 'This account has been deactivated. Please contact an administrator.',
                    'email_value': email,
                })
        else:
            return render(request, self.template_name, {
                'error': 'No account found with that email and password. Please check your credentials.',
                'email_value': email,
            })


class LogoutView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        messages.success(request, 'You have been signed out successfully.')
        return redirect('accounts:home')


class SignupView(View):
    template_name = 'accounts/signup.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')

        data = {
            'email': request.POST.get('email', '').strip().lower(),
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'role': request.POST.get('role', 'STUDENT'),
            'password1': request.POST.get('password1', ''),
            'password2': request.POST.get('password2', ''),
        }

        errors = {}
        if not data['email']: errors['email'] = 'Email is required.'
        elif CustomUser.objects.filter(email=data['email']).exists():
            errors['email'] = 'An account with this email already exists.'
        if not data['first_name']: errors['first_name'] = 'First name is required.'
        if not data['last_name']: errors['last_name'] = 'Last name is required.'
        if not data['password1']: errors['password1'] = 'Password is required.'
        elif len(data['password1']) < 8: errors['password1'] = 'Password must be at least 8 characters.'
        if data['password1'] != data['password2']: errors['password2'] = 'Passwords do not match.'
        if data['role'] not in ['STUDENT', 'TEACHER', 'ADMIN']: data['role'] = 'STUDENT'

        if errors:
            return render(request, self.template_name, {'errors': errors, 'form_data': data})

        try:
            user = CustomUser.objects.create_user(
                email=data['email'],
                password=data['password1'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data['role'],
            )
            login(request, user)
            messages.success(request, f'Welcome to Smart University, {user.get_full_name()}! Account created successfully.')
            return redirect('accounts:dashboard')
        except Exception as e:
            logger.error(f"Signup error: {e}")
            return render(request, self.template_name, {
                'errors': {'general': f'Could not create account. Please try again.'},
                'form_data': data,
            })


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        context = self._build_context(user)
        template = f'accounts/dashboard_{user.role.lower()}.html'
        return render(request, template, context)

    def _build_context(self, user):
        from enrollment.models import Enrollment
        from attendance.models import Attendance
        from academics.models import CourseAssignment, Department, Course

        ctx = {'user': user}

        if user.is_admin:
            ctx.update({
                'total_students': CustomUser.objects.filter(role='STUDENT').count(),
                'total_teachers': CustomUser.objects.filter(role='TEACHER').count(),
                'total_departments': Department.objects.count(),
                'total_courses': Course.objects.count(),
                'recent_users': CustomUser.objects.order_by('-created_at')[:8],
            })
        elif user.is_teacher:
            try:
                assignments = CourseAssignment.objects.filter(
                    teacher=user.teacher_profile
                ).select_related('course', 'course__department').prefetch_related('enrollments')
                ctx.update({
                    'assignments': assignments,
                    'total_students': sum(a.enrollments.count() for a in assignments),
                })
            except Exception:
                ctx.update({'assignments': [], 'total_students': 0})
        elif user.is_student:
            try:
                profile = user.student_profile
                enrollments = Enrollment.objects.filter(student=profile).select_related(
                    'course_assignment__course', 'course_assignment__teacher__user')
                ctx.update({
                    'profile': profile,
                    'enrollments': enrollments,
                    'cgpa': profile.get_cgpa(),
                    'attendance_summary': Attendance.get_student_summary(profile),
                })
            except StudentProfile.DoesNotExist:
                ctx['profile'] = None
        return ctx


# ── User Management ──────────────────────────────────────────────────────────

class UserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by('-created_at')
        role = self.request.GET.get('role')
        search = self.request.GET.get('search', '').strip()
        if role: qs = qs.filter(role=role)
        if search:
            qs = qs.filter(first_name__icontains=search) | \
                 qs.filter(last_name__icontains=search) | \
                 qs.filter(email__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'roles': CustomUser.Role.choices,
                    'selected_role': self.request.GET.get('role', ''),
                    'search': self.request.GET.get('search', '')})
        return ctx


class UserCreateView(AdminRequiredMixin, View):
    template_name = 'accounts/user_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'user_form': UserCreateForm(), 'student_form': StudentProfileForm(),
            'teacher_form': TeacherProfileForm(), 'action': 'Create',
        })

    def post(self, request):
        user_form = UserCreateForm(request.POST)
        student_form = StudentProfileForm(request.POST, request.FILES)
        teacher_form = TeacherProfileForm(request.POST)
        if user_form.is_valid():
            role = user_form.cleaned_data['role']
            with transaction.atomic():
                user = user_form.save()
                if role == 'STUDENT' and student_form.is_valid():
                    p = student_form.save(commit=False); p.user = user; p.save()
                    messages.success(request, f'Student {user.get_full_name()} created successfully.')
                    return redirect('accounts:user_list')
                elif role == 'TEACHER' and teacher_form.is_valid():
                    p = teacher_form.save(commit=False); p.user = user; p.save()
                    messages.success(request, f'Teacher {user.get_full_name()} created successfully.')
                    return redirect('accounts:user_list')
                elif role == 'ADMIN':
                    messages.success(request, f'Admin {user.get_full_name()} created successfully.')
                    return redirect('accounts:user_list')
                else:
                    user.delete()
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'user_form': user_form, 'student_form': student_form,
            'teacher_form': teacher_form, 'action': 'Create',
        })


class UserDetailView(AdminRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/user_detail.html'
    context_object_name = 'target_user'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.get_object()
        ctx['profile'] = getattr(u, 'student_profile' if u.is_student else 'teacher_profile', None)
        return ctx


class UserUpdateView(AdminRequiredMixin, View):
    template_name = 'accounts/user_form.html'

    def get(self, request, pk):
        target = get_object_or_404(CustomUser, pk=pk)
        ctx = {'user_form': UserUpdateForm(instance=target), 'target_user': target, 'action': 'Update'}
        if target.is_student: ctx['student_form'] = StudentProfileForm(instance=getattr(target, 'student_profile', None))
        elif target.is_teacher: ctx['teacher_form'] = TeacherProfileForm(instance=getattr(target, 'teacher_profile', None))
        return render(request, self.template_name, ctx)

    def post(self, request, pk):
        target = get_object_or_404(CustomUser, pk=pk)
        user_form = UserUpdateForm(request.POST, instance=target)
        if user_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                if target.is_student:
                    sf = StudentProfileForm(request.POST, request.FILES, instance=getattr(target, 'student_profile', None))
                    if sf.is_valid(): p = sf.save(commit=False); p.user = user; p.save()
                elif target.is_teacher:
                    tf = TeacherProfileForm(request.POST, instance=getattr(target, 'teacher_profile', None))
                    if tf.is_valid(): p = tf.save(commit=False); p.user = user; p.save()
                messages.success(request, 'User updated successfully.')
                return redirect('accounts:user_detail', pk=pk)
        messages.error(request, 'Please correct the errors.')
        return render(request, self.template_name, {'user_form': user_form, 'target_user': target, 'action': 'Update'})


class UserToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, 'You cannot deactivate your own account.')
        else:
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            messages.success(request, f'User {"activated" if user.is_active else "deactivated"} successfully.')
        return redirect('accounts:user_detail', pk=pk)


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'
    def get(self, request):
        return render(request, self.template_name, {'target_user': request.user})


class ChangePasswordView(LoginRequiredMixin, View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ChangePasswordForm()})

    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['old_password']):
                messages.error(request, 'Incorrect current password.')
            else:
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


# ── Error handlers ────────────────────────────────────────────────────────────
def error_403(request, exception=None): return render(request, 'errors/403.html', status=403)
def error_404(request, exception=None): return render(request, 'errors/404.html', status=404)
def error_500(request): return render(request, 'errors/500.html', status=500)
