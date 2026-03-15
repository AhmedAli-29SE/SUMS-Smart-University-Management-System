from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Base mixin that restricts views to users with specific roles.
    Usage: set `allowed_roles = ['ADMIN', 'TEACHER']` on your view.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Restricts access to Admin users only."""
    allowed_roles = ['ADMIN']


class TeacherRequiredMixin(RoleRequiredMixin):
    """Restricts access to Teacher users only."""
    allowed_roles = ['TEACHER']


class StudentRequiredMixin(RoleRequiredMixin):
    """Restricts access to Student users only."""
    allowed_roles = ['STUDENT']


class AdminOrTeacherMixin(RoleRequiredMixin):
    """Allows both Admin and Teacher access."""
    allowed_roles = ['ADMIN', 'TEACHER']
