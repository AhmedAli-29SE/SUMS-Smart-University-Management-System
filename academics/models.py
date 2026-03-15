from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['code'])]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_active_courses_count(self):
        return self.courses.filter(is_active=True).count()

    def get_student_count(self):
        return self.students.count()


class Course(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=15, unique=True)
    credit_hours = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        indexes = [models.Index(fields=['code'])]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.credit_hours} cr)"


class CourseAssignment(models.Model):
    """Maps a teacher to a course for a specific semester/year."""
    class Semester(models.IntegerChoices):
        FIRST = 1, '1st Semester'
        SECOND = 2, '2nd Semester'
        THIRD = 3, '3rd Semester'
        FOURTH = 4, '4th Semester'
        FIFTH = 5, '5th Semester'
        SIXTH = 6, '6th Semester'
        SEVENTH = 7, '7th Semester'
        EIGHTH = 8, '8th Semester'

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    teacher = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='course_assignments'
    )
    semester = models.IntegerField(choices=Semester.choices)
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures one teacher per course per semester per year
        unique_together = [['course', 'semester', 'year']]
        ordering = ['-year', 'semester']
        indexes = [
            models.Index(fields=['semester', 'year']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'semester', 'year'],
                name='unique_course_assignment'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            exists = CourseAssignment.objects.filter(
                course=self.course,
                semester=self.semester,
                year=self.year
            ).exists()
            if exists:
                from django.db import IntegrityError
                raise IntegrityError("Assignment for this course, semester and year already exists.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.code} | Sem {self.semester} {self.year} | {self.teacher.user.get_full_name()}"

    def get_enrolled_count(self):
        return self.enrollments.count()

    def get_attendance_percentage(self):
        from attendance.models import Attendance
        total = Attendance.objects.filter(
            enrollment__course_assignment=self
        ).count()
        present = Attendance.objects.filter(
            enrollment__course_assignment=self,
            status=Attendance.Status.PRESENT
        ).count()
        return round((present / total * 100), 1) if total else 0
