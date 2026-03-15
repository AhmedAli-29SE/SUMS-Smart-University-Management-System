"""
Management command to seed initial demo data.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Seed the database with initial demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        with transaction.atomic():
            self._seed_departments()
            self._seed_users()
            self._seed_courses()
            self._seed_assignments()
        self.stdout.write(self.style.SUCCESS('Data seeded successfully!'))
        self._print_credentials()

    def _seed_departments(self):
        from academics.models import Department
        depts = [
            ('Computer Science', 'CS'),
            ('Mathematics', 'MATH'),
            ('Physics', 'PHY'),
            ('Electrical Engineering', 'EE'),
        ]
        for name, code in depts:
            Department.objects.get_or_create(code=code, defaults={'name': name})
        self.stdout.write(f'  Created {len(depts)} departments')

    def _seed_users(self):
        from django.contrib.auth import get_user_model
        from academics.models import Department
        from accounts.models import StudentProfile, TeacherProfile

        User = get_user_model()

        # Admin
        admin, _ = User.objects.get_or_create(
            email='admin@university.edu',
            defaults={'first_name': 'System', 'last_name': 'Admin', 'role': 'ADMIN', 'is_staff': True}
        )
        admin.set_password('Admin@123')
        admin.save()

        cs = Department.objects.get(code='CS')
        math = Department.objects.get(code='MATH')

        # Teacher
        teacher, _ = User.objects.get_or_create(
            email='teacher@university.edu',
            defaults={'first_name': 'John', 'last_name': 'Smith', 'role': 'TEACHER'}
        )
        teacher.set_password('Teacher@123')
        teacher.save()
        TeacherProfile.objects.get_or_create(
            user=teacher,
            defaults={'employee_id': 'EMP001', 'department': cs, 'designation': 'ASST_PROF'}
        )

        # Math Teacher
        mteacher, _ = User.objects.get_or_create(
            email='maths@university.edu',
            defaults={'first_name': 'Jane', 'last_name': 'Doe', 'role': 'TEACHER'}
        )
        mteacher.set_password('Teacher@123')
        mteacher.save()
        TeacherProfile.objects.get_or_create(
            user=mteacher,
            defaults={'employee_id': 'EMP002', 'department': math, 'designation': 'PROFESSOR'}
        )

        # Student
        student, _ = User.objects.get_or_create(
            email='student@university.edu',
            defaults={'first_name': 'Alice', 'last_name': 'Johnson', 'role': 'STUDENT'}
        )
        student.set_password('Student@123')
        student.save()
        StudentProfile.objects.get_or_create(
            user=student,
            defaults={
                'registration_number': 'CS2024001',
                'department': cs,
                'semester': 1,
                'session': '2024-2028',
            }
        )

        self.stdout.write('  Created demo users')

    def _seed_courses(self):
        from academics.models import Course, Department
        cs = Department.objects.get(code='CS')
        math = Department.objects.get(code='MATH')

        courses = [
            ('Introduction to Programming', 'CS101', 3, cs),
            ('Data Structures', 'CS201', 3, cs),
            ('Database Systems', 'CS301', 3, cs),
            ('Calculus I', 'MATH101', 4, math),
            ('Linear Algebra', 'MATH201', 3, math),
        ]
        for name, code, credits, dept in courses:
            Course.objects.get_or_create(code=code, defaults={'name': name, 'credit_hours': credits, 'department': dept})
        self.stdout.write(f'  Created {len(courses)} courses')

    def _seed_assignments(self):
        from academics.models import Course, CourseAssignment
        from accounts.models import TeacherProfile
        from django.contrib.auth import get_user_model
        User = get_user_model()

        teacher = TeacherProfile.objects.get(employee_id='EMP001')
        mteacher = TeacherProfile.objects.get(employee_id='EMP002')

        assignments = [
            ('CS101', teacher, 1, 2024),
            ('CS201', teacher, 2, 2024),
            ('MATH101', mteacher, 1, 2024),
        ]
        for code, t, sem, year in assignments:
            course = Course.objects.get(code=code)
            CourseAssignment.objects.get_or_create(
                course=course, semester=sem, year=year,
                defaults={'teacher': t}
            )
        self.stdout.write(f'  Created {len(assignments)} assignments')

    def _print_credentials(self):
        self.stdout.write('\n' + '-' * 50)
        self.stdout.write(self.style.SUCCESS('Demo Credentials:'))
        self.stdout.write('  Admin:   admin@university.edu / Admin@123')
        self.stdout.write('  Teacher: teacher@university.edu / Teacher@123')
        self.stdout.write('  Student: student@university.edu / Student@123')
        self.stdout.write('-' * 50)
