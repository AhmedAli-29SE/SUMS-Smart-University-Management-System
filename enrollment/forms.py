from django import forms
from .models import Enrollment
from academics.models import CourseAssignment


class EnrollmentForm(forms.Form):
    """
    Student-facing form to select a CourseAssignment to enroll in.
    Filters by the student's department and semester.
    """
    course_assignment = forms.ModelChoiceField(
        queryset=CourseAssignment.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Select Course'
    )

    def __init__(self, student_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get already-enrolled assignment IDs
        enrolled_ids = Enrollment.objects.filter(
            student=student_profile
        ).values_list('course_assignment_id', flat=True)

        self.fields['course_assignment'].queryset = CourseAssignment.objects.filter(
            semester=student_profile.semester,
            is_active=True,
            course__department=student_profile.department,
        ).exclude(
            id__in=enrolled_ids
        ).select_related('course__department', 'teacher__user')
