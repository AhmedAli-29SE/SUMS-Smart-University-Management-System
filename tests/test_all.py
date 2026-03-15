"""
Smart University Management System - Comprehensive Test Suite
Run: python manage.py test tests --verbosity=2
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


# ── Helpers ────────────────────────────────────────────────────

def make_user(email, role, pw='TestPass1!'):
    user, created = User.objects.get_or_create(
        email=email,
        defaults={'first_name': 'Test', 'last_name': role.title(), 'role': role}
    )
    user.set_password(pw)
    user.save()

    # Ensure role profile exists with unique ID
    from academics.models import Department
    dept, _ = Department.objects.get_or_create(name='Test Dept', defaults={'code': 'TDEPT'})
    suffix = email.split('@')[0][-4:]
    if role == 'STUDENT':
        from accounts.models import StudentProfile
        if not hasattr(user, 'student_profile'):
            StudentProfile.objects.create(
                user=user, registration_number=f'REG-{suffix}', department=dept, semester=1
            )
    elif role == 'TEACHER':
        from accounts.models import TeacherProfile
        if not hasattr(user, 'teacher_profile'):
            TeacherProfile.objects.create(
                user=user, employee_id=f'EMP-{suffix}', department=dept
            )
    return user


def make_dept(name='CS', code='CS'):
    from academics.models import Department
    return Department.objects.create(name=f'{name} Dept', code=code)


def make_course(dept, code='CS101', credits=3):
    from academics.models import Course
    return Course.objects.create(
        name='Intro to Programming', code=code,
        credit_hours=credits, department=dept,
    )


def make_assignment(course, teacher_profile, sem=1, year=2024):
    from academics.models import CourseAssignment
    return CourseAssignment.objects.create(
        course=course, teacher=teacher_profile, semester=sem, year=year
    )


def make_student(user, dept, sem=1):
    from accounts.models import StudentProfile
    p, _ = StudentProfile.objects.get_or_create(
        user=user,
        defaults={
            'registration_number': f'REG-{user.email.split("@")[0][-4:]}',
            'department': dept, 'semester': sem, 'session': '2024-2028'
        }
    )
    return p


def make_teacher(user, dept):
    from accounts.models import TeacherProfile
    suffix = user.email.split('@')[0][-4:]
    p, _ = TeacherProfile.objects.get_or_create(
        user=user, defaults={'employee_id': f'EMP-{suffix}', 'department': dept}
    )
    return p


def make_enrollment(student, assignment):
    from enrollment.models import Enrollment
    return Enrollment.objects.create(student=student, course_assignment=assignment)


# ── CustomUser Model Tests ─────────────────────────────────────

class CustomUserTests(TestCase):
    def test_create_user(self):
        u = make_user('s@x.com', 'STUDENT')
        self.assertEqual(u.email, 's@x.com')
        self.assertTrue(u.is_active)

    def test_role_properties(self):
        self.assertTrue(make_user('a@x.com', 'ADMIN').is_admin)
        self.assertTrue(make_user('t@x.com', 'TEACHER').is_teacher)
        self.assertTrue(make_user('s2@x.com', 'STUDENT').is_student)

    def test_email_uniqueness(self):
        make_user('dup@x.com', 'STUDENT')
        with self.assertRaises(Exception):
            User.objects.create_user(email='dup@x.com', password='x')

    def test_str_contains_email(self):
        u = make_user('me@x.com', 'ADMIN')
        self.assertIn('me@x.com', str(u))


# ── Result / GPA Calculation Tests ─────────────────────────────

class ResultCalculationTests(TestCase):
    def setUp(self):
        from results.models import Result
        self.Result = Result
        self.dept = make_dept()
        tu = make_user('teach@x.com', 'TEACHER')
        su = make_user('stud@x.com', 'STUDENT')
        self.teacher = make_teacher(tu, self.dept)
        self.student = make_student(su, self.dept)
        self.course = make_course(self.dept, credits=3)
        self.assignment = make_assignment(self.course, self.teacher)
        self.enrollment = make_enrollment(self.student, self.assignment)

    def test_grade_thresholds(self):
        cases = [
            (95, 'A+'), (90, 'A'), (85, 'A-'), (80, 'B+'),
            (75, 'B'), (70, 'B-'), (65, 'C+'), (60, 'C'),
            (55, 'C-'), (50, 'D'), (49, 'F'),
        ]
        for marks, expected in cases:
            self.assertEqual(self.Result.compute_grade(marks), expected, f'Failed for {marks}')

    def test_auto_total_on_save(self):
        r = self.Result.objects.create(
            enrollment=self.enrollment,
            midterm_marks=Decimal('25'),
            final_marks=Decimal('40'),
            assignment_marks=Decimal('18'),
        )
        self.assertEqual(float(r.total), 83.0)

    def test_auto_grade_on_save(self):
        r = self.Result.objects.create(
            enrollment=self.enrollment,
            midterm_marks=25, final_marks=40, assignment_marks=18,
        )
        self.assertEqual(r.grade, 'B+')

    def test_gpa_points_assigned(self):
        r = self.Result.objects.create(
            enrollment=self.enrollment,
            midterm_marks=28, final_marks=45, assignment_marks=20,
        )
        # 93 → A → 4.0
        self.assertEqual(float(r.gpa_points), 4.0)

    def test_cgpa_calculation(self):
        self.Result.objects.create(
            enrollment=self.enrollment,
            midterm_marks=28, final_marks=45, assignment_marks=20,
        )
        cgpa = self.Result.get_cgpa(self.student)
        self.assertGreater(cgpa, 0)

    def test_semester_gpa(self):
        self.Result.objects.create(
            enrollment=self.enrollment,
            midterm_marks=25, final_marks=40, assignment_marks=15,
        )
        gpa = self.Result.get_semester_gpa(self.student, semester=1, year=2024)
        self.assertGreater(gpa, 0)


# ── Enrollment Tests ───────────────────────────────────────────

class EnrollmentTests(TestCase):
    def setUp(self):
        self.dept = make_dept()
        tu = make_user('teach2@x.com', 'TEACHER')
        su = make_user('stud2@x.com', 'STUDENT')
        self.teacher = make_teacher(tu, self.dept)
        self.student = make_student(su, self.dept)
        self.course = make_course(self.dept, code='CS102')
        self.assignment = make_assignment(self.course, self.teacher)

    def test_create_enrollment(self):
        from enrollment.models import Enrollment
        e = Enrollment.objects.create(student=self.student, course_assignment=self.assignment)
        self.assertIsNotNone(e.pk)

    def test_duplicate_enrollment_prevented(self):
        from enrollment.models import Enrollment
        from django.db import IntegrityError
        Enrollment.objects.create(student=self.student, course_assignment=self.assignment)
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student, course_assignment=self.assignment)


# ── CourseAssignment Uniqueness Tests ──────────────────────────

class CourseAssignmentTests(TestCase):
    def setUp(self):
        from academics.models import CourseAssignment
        self.CourseAssignment = CourseAssignment
        self.dept = make_dept('Physics', 'PHY')
        tu1 = make_user('t1@x.com', 'TEACHER')
        tu2 = make_user('t2@x.com', 'TEACHER')
        self.t1 = make_teacher(tu1, self.dept)
        self.t2 = make_teacher(tu2, self.dept)
        self.course = make_course(self.dept, code='PHY101')

    def test_duplicate_assignment_blocked(self):
        from django.db import IntegrityError
        self.CourseAssignment.objects.create(
            course=self.course, teacher=self.t1,
            semester=1, year=2024
        )
        with self.assertRaises(IntegrityError):
            self.CourseAssignment.objects.create(
                course=self.course, teacher=self.t2,
                semester=1, year=2024
            )

    def test_different_year_allowed(self):
        make_assignment(self.course, self.t1, sem=1, year=2024)
        a2 = make_assignment(self.course, self.t1, sem=1, year=2025)
        self.assertIsNotNone(a2.pk)


# ── Attendance Tests ───────────────────────────────────────────

class AttendanceTests(TestCase):
    def setUp(self):
        from datetime import date
        self.dept = make_dept('Math', 'MTH')
        tu = make_user('tm@x.com', 'TEACHER')
        su = make_user('sm@x.com', 'STUDENT')
        teacher = make_teacher(tu, self.dept)
        student = make_student(su, self.dept)
        course = make_course(self.dept, code='MTH101')
        assignment = make_assignment(course, teacher)
        self.enrollment = make_enrollment(student, assignment)
        self.today = date.today()
        self.teacher_user = tu

    def test_create_attendance(self):
        from attendance.models import Attendance
        a = Attendance.objects.create(
            enrollment=self.enrollment,
            date=self.today,
            status='PRESENT',
            marked_by=self.teacher_user,
        )
        self.assertEqual(a.status, 'PRESENT')
        self.assertTrue(a.is_present)

    def test_duplicate_attendance_prevented(self):
        from attendance.models import Attendance
        from django.db import IntegrityError
        Attendance.objects.create(enrollment=self.enrollment, date=self.today, status='PRESENT')
        with self.assertRaises(IntegrityError):
            Attendance.objects.create(enrollment=self.enrollment, date=self.today, status='ABSENT')

    def test_attendance_percentage(self):
        from attendance.models import Attendance
        from datetime import date, timedelta
        for i in range(8):
            Attendance.objects.create(
                enrollment=self.enrollment,
                date=self.today - timedelta(days=i),
                status='PRESENT' if i < 6 else 'ABSENT',
            )
        pct = self.enrollment.get_attendance_percentage()
        self.assertEqual(pct, 75.0)


# ── Authentication / View Access Tests ────────────────────────

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_page_loads(self):
        resp = self.client.get(reverse('accounts:login'))
        self.assertEqual(resp.status_code, 200)

    def test_redirect_unauthenticated_to_login(self):
        resp = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(resp, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_login_with_valid_credentials(self):
        make_user('login@x.com', 'ADMIN', 'GoodPass1!')
        resp = self.client.post(reverse('accounts:login'), {
            'email': 'login@x.com',
            'password': 'GoodPass1!',
        })
        self.assertRedirects(resp, reverse('accounts:dashboard'))

    def test_login_invalid_credentials(self):
        resp = self.client.post(reverse('accounts:login'), {
            'email': 'no@x.com',
            'password': 'wrongpass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'No account found with that email')


# ── Role-Based Access Control Tests ───────────────────────────

class RBACTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin@rbac.com', 'ADMIN')
        self.teacher = make_user('teacher@rbac.com', 'TEACHER')
        self.student = make_user('student@rbac.com', 'STUDENT')

    def test_admin_can_access_user_list(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(resp.status_code, 200)

    def test_student_cannot_access_user_list(self):
        self.client.force_login(self.student)
        resp = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(resp.status_code, 403)

    def test_teacher_cannot_access_user_list(self):
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_create_user(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('accounts:user_create'))
        self.assertEqual(resp.status_code, 200)

    def test_student_enrollment_page_visible(self):
        dept = make_dept()
        su_profile = make_student(self.student, dept)
        self.client.force_login(self.student)
        resp = self.client.get(reverse('enrollment:my_enrollments'))
        self.assertEqual(resp.status_code, 200)

    def test_teacher_mark_attendance_accessible(self):
        dept = make_dept('IT', 'IT')
        tp = make_teacher(self.teacher, dept)
        self.client.force_login(self.teacher)
        resp = self.client.get(reverse('attendance:mark_select'))
        self.assertEqual(resp.status_code, 200)


# ── Department & Course Tests ──────────────────────────────────

class AcademicsTests(TestCase):
    def test_department_creation(self):
        dept = make_dept('Engineering', 'ENG')
        self.assertEqual(dept.code, 'ENG')
        self.assertTrue(dept.is_active)

    def test_course_linked_to_department(self):
        dept = make_dept()
        course = make_course(dept)
        self.assertEqual(course.department, dept)
        self.assertEqual(course.credit_hours, 3)

    def test_department_course_count(self):
        dept = make_dept()
        make_course(dept, 'CS101')
        make_course(dept, 'CS102')
        self.assertEqual(dept.get_active_courses_count(), 2)
