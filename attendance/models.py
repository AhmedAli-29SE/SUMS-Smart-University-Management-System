from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused'

    enrollment = models.ForeignKey(
        'enrollment.Enrollment',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT
    )
    remarks = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_marked'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One record per enrollment per day
        unique_together = [['enrollment', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['enrollment', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return (
            f"{self.enrollment.student.user.get_full_name()} | "
            f"{self.enrollment.course_assignment.course.code} | "
            f"{self.date} | {self.status}"
        )

    @property
    def is_present(self):
        return self.status in [self.Status.PRESENT, self.Status.LATE]

    @classmethod
    def get_student_summary(cls, student_profile):
        """Returns per-course attendance summary for a student."""
        from django.db.models import Count, Q
        from enrollment.models import Enrollment

        enrollments = Enrollment.objects.filter(
            student=student_profile
        ).prefetch_related('attendance_records')

        summary = []
        for e in enrollments:
            records = e.attendance_records.all()
            total = records.count()
            present = records.filter(status__in=['PRESENT', 'LATE']).count()
            pct = round(present / total * 100, 1) if total else 0.0
            summary.append({
                'course': e.course_assignment.course,
                'total': total,
                'present': present,
                'absent': total - present,
                'percentage': pct,
                'is_short': pct < 75,
            })
        return summary
