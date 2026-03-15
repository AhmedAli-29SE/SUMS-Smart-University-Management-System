# Smart University Management System (SUMS)

A production-ready, role-based university management system built with **Django 5**, **PostgreSQL**, and server-rendered templates. No REST framework — pure Django class-based views, forms, and template inheritance.

---

## 🏗️ Architecture Overview

```
smart_university/
├── config/                 # Project configuration (settings, urls, wsgi)
├── accounts/               # Custom user model, profiles, auth views
│   └── management/
│       └── commands/
│           └── seed_data.py
├── academics/              # Departments, Courses, CourseAssignments
├── enrollment/             # Student enrollment logic
├── attendance/             # Teacher marks attendance per session
├── results/                # Marks entry, GPA/CGPA auto-calculation
├── templates/              # All HTML templates (Jinja-free Django templates)
│   ├── base.html           # Master layout with sidebar navigation
│   ├── accounts/
│   ├── academics/
│   ├── enrollment/
│   ├── attendance/
│   ├── results/
│   └── errors/
├── tests/                  # Comprehensive test suite
├── static/                 # CSS, JS
├── logs/                   # Application logs
├── requirements.txt
├── .env.example
└── manage.py
```

### Key Architectural Decisions

| Decision | Rationale |
|---|---|
| Email as USERNAME_FIELD | More natural for university users; no need for separate username |
| OneToOne profiles (Student/Teacher) | Keeps CustomUser clean; role-specific data isolated |
| Role-based mixins hierarchy | `RoleRequiredMixin → AdminRequiredMixin / TeacherRequiredMixin / StudentRequiredMixin` — composable, DRY |
| Auto-grade calculation in `Result.save()` | Single source of truth; marks → total → grade → GPA points in one operation |
| `unique_together` on CourseAssignment | Enforces "one teacher per course per semester" at DB level |
| `unique_together` on Enrollment | Prevents duplicate enrollments at DB level, not just application level |
| `select_related` / `prefetch_related` everywhere | No N+1 queries in list views |
| WhiteNoise for static files | Serves static files directly from Django in production without Nginx config |

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip

### 2. Clone & Setup

```bash
git clone <repo>
cd smart_university

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

**.env example:**
```
DEBUG=True
SECRET_KEY=your-very-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=smart_university_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Database Setup

```bash
# Create the PostgreSQL database
psql -U postgres -c "CREATE DATABASE smart_university_db;"

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_data

# (Optional) Create superuser for Django admin
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 👤 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@university.edu | Admin@123 |
| Teacher | teacher@university.edu | Teacher@123 |
| Student | student@university.edu | Student@123 |

---

## 🔐 Role-Based Access Control

| Feature | Admin | Teacher | Student |
|---------|-------|---------|---------|
| Manage Users | ✅ | ❌ | ❌ |
| Manage Departments | ✅ | View | ❌ |
| Manage Courses | ✅ | View | ❌ |
| Assign Teachers | ✅ | ❌ | ❌ |
| Mark Attendance | ❌ | ✅ | ❌ |
| Enter Marks | ❌ | ✅ | ❌ |
| Enroll in Courses | ❌ | ❌ | ✅ |
| View Attendance | View all | Own courses | Own |
| View Results | View all | Own courses | Own |
| View CGPA | View all | View students | Own |
| Print Transcript | ❌ | ❌ | ✅ |

---

## 📊 GPA / Grading System

### Marks Distribution

| Component | Max Marks |
|-----------|-----------|
| Midterm | 30 |
| Final Exam | 50 |
| Assignments | 20 |
| **Total** | **100** |

### Grade Scale

| Marks | Grade | GPA Points |
|-------|-------|------------|
| 95–100 | A+ | 4.0 |
| 90–94 | A | 4.0 |
| 85–89 | A- | 3.7 |
| 80–84 | B+ | 3.3 |
| 75–79 | B | 3.0 |
| 70–74 | B- | 2.7 |
| 65–69 | C+ | 2.3 |
| 60–64 | C | 2.0 |
| 55–59 | C- | 1.7 |
| 50–54 | D | 1.0 |
| <50 | F | 0.0 |

### CGPA Formula

```
CGPA = Σ(GPA_Points × Credit_Hours) / Σ(Credit_Hours)
```

Auto-calculated on every result save via `Result.save()` override.

---

## 🗄️ Database Schema

```
CustomUser (email PK, role, is_active)
    ↓ OneToOne
StudentProfile (reg_number, department, semester, session)
TeacherProfile (employee_id, department, designation)

Department (name, code)
    ↓ FK
Course (name, code, credit_hours)
    ↓ FK
CourseAssignment (course, teacher, semester, year) [unique: course+semester+year]
    ↓ FK
Enrollment (student, course_assignment) [unique: student+course_assignment]
    ↓ FK
Attendance (enrollment, date, status) [unique: enrollment+date]
Result (enrollment, midterm, final, assignment, total, grade, gpa) [OneToOne with Enrollment]
```

---

## 🧪 Running Tests

```bash
python manage.py test tests --verbosity=2
```

**Test coverage includes:**
- CustomUser model creation and role properties
- Result grade calculation (all thresholds)
- Auto-total/grade/GPA assignment on save
- CGPA and semester GPA calculations
- Enrollment duplicate prevention (DB-level)
- CourseAssignment uniqueness enforcement
- Attendance duplicate prevention
- Attendance percentage calculation
- Authentication flow (login/redirect)
- Role-based access control (403 for unauthorized roles)
- Department and course creation

---

## 🚢 Production Deployment

### Environment

```bash
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Static Files

```bash
python manage.py collectstatic --noinput
```

WhiteNoise is configured to serve static files efficiently.

### With Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Nginx (recommended reverse proxy)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| Django 5.0 | Web framework |
| psycopg2-binary | PostgreSQL adapter |
| python-decouple | Environment variable management |
| whitenoise | Static file serving |
| gunicorn | Production WSGI server |
| Pillow | Image handling (profile photos) |
| django-widget-tweaks | Template form rendering utilities |

---

## 🔧 Django Admin

Full admin interface available at `/admin/` for superusers. All models are registered with appropriate search, filter, and list display configurations.

---

## 📝 License

MIT License — Free to use for educational and commercial purposes.
