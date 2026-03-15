from django.db import models


class Enrollment(models.Model):
    """
    Links a StudentProfile to a CourseAssignment.
    Unique constraint prevents duplicate enrollments.
    """
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course_assignment = models.ForeignKey(
        'academics.CourseAssignment',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        # Prevents a student from enrolling in the same course assignment twice
        unique_together = [['student', 'course_assignment']]
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student', 'course_assignment']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course_assignment'],
                name='unique_student_enrollment'
            )
        ]

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} → "
            f"{self.course_assignment.course.code} "
            f"(Sem {self.course_assignment.semester}, {self.course_assignment.year})"
        )

    def get_attendance_percentage(self):
        total = self.attendance_records.count()
        if not total:
            return 0.0
        present = self.attendance_records.filter(status='PRESENT').count()
        return round(present / total * 100, 1)

    def get_result(self):
        return getattr(self, 'result', None)
