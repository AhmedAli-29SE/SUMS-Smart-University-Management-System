from django import forms
from .models import Department, Course, CourseAssignment


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        return self.cleaned_data['code'].upper()


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'code', 'credit_hours', 'department', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'credit_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        return self.cleaned_data['code'].upper()


class CourseAssignmentForm(forms.ModelForm):
    class Meta:
        model = CourseAssignment
        fields = ['course', 'teacher', 'semester', 'year', 'is_active']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import TeacherProfile
        self.fields['teacher'].queryset = TeacherProfile.objects.select_related(
            'user', 'department'
        ).filter(user__is_active=True)
        self.fields['course'].queryset = Course.objects.select_related(
            'department'
        ).filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get('course')
        semester = cleaned.get('semester')
        year = cleaned.get('year')

        if course and semester and year:
            qs = CourseAssignment.objects.filter(
                course=course, semester=semester, year=year
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"{course.code} already has a teacher assigned for Semester {semester}, {year}."
                )
        return cleaned
