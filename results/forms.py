from django import forms
from .models import Result


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['midterm_marks', 'final_marks', 'assignment_marks']
        widgets = {
            'midterm_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'max': 30, 'step': '0.5',
                'placeholder': 'Out of 30'
            }),
            'final_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'max': 50, 'step': '0.5',
                'placeholder': 'Out of 50'
            }),
            'assignment_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'max': 20, 'step': '0.5',
                'placeholder': 'Out of 20'
            }),
        }
        labels = {
            'midterm_marks': 'Midterm Marks (Max: 30)',
            'final_marks': 'Final Marks (Max: 50)',
            'assignment_marks': 'Assignment Marks (Max: 20)',
        }

    def clean_midterm_marks(self):
        val = self.cleaned_data.get('midterm_marks')
        if val is not None and not (0 <= float(val) <= 30):
            raise forms.ValidationError('Midterm marks must be between 0 and 30.')
        return val

    def clean_final_marks(self):
        val = self.cleaned_data.get('final_marks')
        if val is not None and not (0 <= float(val) <= 50):
            raise forms.ValidationError('Final marks must be between 0 and 50.')
        return val

    def clean_assignment_marks(self):
        val = self.cleaned_data.get('assignment_marks')
        if val is not None and not (0 <= float(val) <= 20):
            raise forms.ValidationError('Assignment marks must be between 0 and 20.')
        return val
