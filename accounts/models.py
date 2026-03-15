from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model using email as the primary identifier.
    Role-based system: Admin, Teacher, Student.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        TEACHER = 'TEACHER', _('Teacher')
        STUDENT = 'STUDENT', _('Student')

    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    def get_role_display_badge(self):
        badges = {
            self.Role.ADMIN: 'danger',
            self.Role.TEACHER: 'primary',
            self.Role.STUDENT: 'success',
        }
        return badges.get(self.role, 'secondary')


class StudentProfile(models.Model):
    """Extended profile for students."""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    registration_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='students'
    )
    semester = models.PositiveSmallIntegerField(default=1)
    session = models.CharField(max_length=20, help_text='e.g. 2023-2027')
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        indexes = [models.Index(fields=['registration_number'])]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.registration_number}"

    def get_cgpa(self):
        """Calculate cumulative GPA across all semesters."""
        from results.models import Result
        results = Result.objects.filter(
            enrollment__student=self,
            gpa_points__isnull=False
        ).select_related('enrollment__course_assignment')

        if not results.exists():
            return 0.0

        total_weighted = sum(
            r.gpa_points * r.enrollment.course_assignment.course.credit_hours
            for r in results
        )
        total_credits = sum(
            r.enrollment.course_assignment.course.credit_hours
            for r in results
        )
        return round(total_weighted / total_credits, 2) if total_credits else 0.0


class TeacherProfile(models.Model):
    """Extended profile for teachers."""
    class Designation(models.TextChoices):
        LECTURER = 'LECTURER', _('Lecturer')
        ASSISTANT_PROFESSOR = 'ASST_PROF', _('Assistant Professor')
        ASSOCIATE_PROFESSOR = 'ASSOC_PROF', _('Associate Professor')
        PROFESSOR = 'PROFESSOR', _('Professor')
        HOD = 'HOD', _('Head of Department')

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='teachers'
    )
    designation = models.CharField(
        max_length=15,
        choices=Designation.choices,
        default=Designation.LECTURER
    )
    phone = models.CharField(max_length=20, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'
        indexes = [models.Index(fields=['employee_id'])]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.designation})"
