from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class Result(models.Model):
    """
    Stores marks for a student's enrollment.
    Total, grade, and GPA are auto-calculated via model save().
    """
    class Grade(models.TextChoices):
        A_PLUS = 'A+', 'A+'
        A = 'A', 'A'
        A_MINUS = 'A-', 'A-'
        B_PLUS = 'B+', 'B+'
        B = 'B', 'B'
        B_MINUS = 'B-', 'B-'
        C_PLUS = 'C+', 'C+'
        C = 'C', 'C'
        C_MINUS = 'C-', 'C-'
        D = 'D', 'D'
        F = 'F', 'F (Fail)'

    # GPA scale: A+ = 4.0, A = 4.0, A- = 3.7, etc.
    GRADE_GPA_MAP = {
        'A+': 4.0, 'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D': 1.0, 'F': 0.0,
    }

    enrollment = models.OneToOneField(
        'enrollment.Enrollment',
        on_delete=models.CASCADE,
        related_name='result'
    )
    midterm_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(30)],
        null=True, blank=True,
        help_text='Out of 30'
    )
    final_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        null=True, blank=True,
        help_text='Out of 50'
    )
    assignment_marks = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        null=True, blank=True,
        help_text='Out of 20'
    )

    # Auto-calculated fields
    total = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=3, choices=Grade.choices, blank=True)
    gpa_points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    entered_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='results_entered'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['enrollment'])]

    def __str__(self):
        return (
            f"{self.enrollment.student.user.get_full_name()} | "
            f"{self.enrollment.course_assignment.course.code} | "
            f"Total: {self.total} | Grade: {self.grade}"
        )

    @staticmethod
    def compute_grade(total):
        """Compute letter grade from total marks (out of 100)."""
        if total is None:
            return ''
        t = float(total)
        if t >= 95: return 'A+'
        if t >= 90: return 'A'
        if t >= 85: return 'A-'
        if t >= 80: return 'B+'
        if t >= 75: return 'B'
        if t >= 70: return 'B-'
        if t >= 65: return 'C+'
        if t >= 60: return 'C'
        if t >= 55: return 'C-'
        if t >= 50: return 'D'
        return 'F'

    def calculate_and_save(self):
        """Recalculate total, grade, and GPA points, then save."""
        mid = float(self.midterm_marks or 0)
        fin = float(self.final_marks or 0)
        asgn = float(self.assignment_marks or 0)

        # Only calculate if at least one value is set
        if self.midterm_marks is not None or self.final_marks is not None or self.assignment_marks is not None:
            self.total = round(mid + fin + asgn, 2)
            self.grade = self.compute_grade(self.total)
            self.gpa_points = self.GRADE_GPA_MAP.get(self.grade, 0.0)

        self.save(update_fields=['total', 'grade', 'gpa_points', 'updated_at'])

    def save(self, *args, **kwargs):
        # Auto-calculate when saving with marks
        if 'update_fields' not in kwargs:
            mid = float(self.midterm_marks or 0)
            fin = float(self.final_marks or 0)
            asgn = float(self.assignment_marks or 0)

            if any([self.midterm_marks, self.final_marks, self.assignment_marks]):
                self.total = round(mid + fin + asgn, 2)
                self.grade = self.compute_grade(self.total)
                self.gpa_points = self.GRADE_GPA_MAP.get(self.grade, 0.0)

        super().save(*args, **kwargs)

    def get_grade_color(self):
        colors = {
            'A+': 'success', 'A': 'success', 'A-': 'success',
            'B+': 'primary', 'B': 'primary', 'B-': 'primary',
            'C+': 'info', 'C': 'info', 'C-': 'info',
            'D': 'warning', 'F': 'danger',
        }
        return colors.get(self.grade, 'secondary')

    @classmethod
    def get_semester_gpa(cls, student_profile, semester, year):
        """Calculate GPA for a specific semester."""
        results = cls.objects.filter(
            enrollment__student=student_profile,
            enrollment__course_assignment__semester=semester,
            enrollment__course_assignment__year=year,
            gpa_points__isnull=False
        ).select_related('enrollment__course_assignment__course')

        if not results.exists():
            return 0.0

        total_weighted = sum(
            float(r.gpa_points) * r.enrollment.course_assignment.course.credit_hours
            for r in results
        )
        total_credits = sum(
            r.enrollment.course_assignment.course.credit_hours
            for r in results
        )
        return round(total_weighted / total_credits, 2) if total_credits else 0.0

    @classmethod
    def get_cgpa(cls, student_profile):
        """Calculate cumulative GPA across all semesters."""
        results = cls.objects.filter(
            enrollment__student=student_profile,
            gpa_points__isnull=False
        ).select_related('enrollment__course_assignment__course')

        if not results.exists():
            return 0.0

        total_weighted = sum(
            float(r.gpa_points) * r.enrollment.course_assignment.course.credit_hours
            for r in results
        )
        total_credits = sum(
            r.enrollment.course_assignment.course.credit_hours
            for r in results
        )
        return round(total_weighted / total_credits, 2) if total_credits else 0.0
