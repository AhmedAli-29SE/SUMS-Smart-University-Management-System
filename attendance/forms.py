from django import forms
from django.utils import timezone
from .models import Attendance
from enrollment.models import Enrollment


class AttendanceDateForm(forms.Form):
    """Teacher selects date to mark attendance."""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now().date
    )


class BulkAttendanceForm(forms.Form):
    """
    Dynamically generated form for marking attendance for all students
    in a course assignment on a given date.
    """
    def __init__(self, enrollments, date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enrollments = enrollments
        self.date = date

        for enrollment in enrollments:
            # Check if attendance already marked
            existing = Attendance.objects.filter(
                enrollment=enrollment, date=date
            ).first()
            initial = existing.status if existing else Attendance.Status.PRESENT

            self.fields[f'status_{enrollment.pk}'] = forms.ChoiceField(
                choices=Attendance.Status.choices,
                initial=initial,
                widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
                label=enrollment.student.user.get_full_name(),
                required=True,
            )
            self.fields[f'remarks_{enrollment.pk}'] = forms.CharField(
                required=False,
                initial=existing.remarks if existing else '',
                widget=forms.TextInput(attrs={
                    'class': 'form-control form-control-sm',
                    'placeholder': 'Optional remarks',
                }),
                label='Remarks',
            )
