# SETUP GUIDE — Windows (Step by Step)

## ✅ Step 1: Find Your PostgreSQL Password

The error `fe_sendauth: no password supplied` means your `.env` file has no password set.

Open `.env` in the project root and fill in your actual PostgreSQL password:

```
DB_PASSWORD=your_postgres_password_here
```

> **Don't know your postgres password?**
> When you installed PostgreSQL, it asked you to set a password for the `postgres` user.
> If you forgot it, reset it:
> 1. Open **pgAdmin** (installed with PostgreSQL) → right-click `postgres` login → Properties → Password
> 2. OR open **SQL Shell (psql)** from Start Menu → press Enter for all prompts except password

---

## ✅ Step 2: Create the Database

**Option A — Using pgAdmin (GUI):**
1. Open pgAdmin from Start Menu
2. Login with your postgres password
3. Right-click `Databases` → `Create` → `Database`
4. Name it: `smart_university_db` → Save

**Option B — Using SQL Shell (psql):**
1. Open `SQL Shell (psql)` from Start Menu
2. Press Enter for all prompts (Server, Database, Port, Username)
3. Enter your password
4. Type this command and press Enter:
```sql
CREATE DATABASE smart_university_db;
```
5. Type `\q` to exit

**Option C — Add PostgreSQL to PATH, then use PowerShell:**
```powershell
# Find your PostgreSQL bin folder (usually something like):
$env:PATH += ";C:\Program Files\PostgreSQL\16\bin"
psql -U postgres -c "CREATE DATABASE smart_university_db;"
```

---

## ✅ Step 3: Configure .env

Open `.env` in the project folder and set it like this:

```
DEBUG=True
SECRET_KEY=django-insecure-sums-change-this-key-in-production-2024
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=smart_university_db
DB_USER=postgres
DB_PASSWORD=YOUR_ACTUAL_POSTGRES_PASSWORD
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Replace `YOUR_ACTUAL_POSTGRES_PASSWORD` with the password you set when installing PostgreSQL.

---

## ✅ Step 4: Run Migrations

```powershell
python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: accounts, admin, attendance, auth, contenttypes, enrollment, results, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  ...
```

---

## ✅ Step 5: Seed Demo Data

```powershell
python manage.py seed_data
```

Expected output:
```
Seeding data...
  Created 4 departments
  Created demo users
  Created 5 courses
  Created 3 assignments
--------------------------------------------------
Demo Credentials:
  Admin:   admin@university.edu / Admin@123
  Teacher: teacher@university.edu / Teacher@123
  Student: student@university.edu / Student@123
--------------------------------------------------
```

---

## ✅ Step 6: Start the Server

```powershell
python manage.py runserver
```

Then open your browser: **http://127.0.0.1:8000**

---

## 🆘 Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `fe_sendauth: no password supplied` | Set `DB_PASSWORD` in `.env` |
| `psql is not recognized` | Use pgAdmin GUI instead, or add PostgreSQL to PATH |
| `FATAL: database does not exist` | Create the database first (Step 2) |
| `staticfiles.W004` | Harmless warning — static dir now auto-created |
| `FATAL: password authentication failed` | Wrong password in `.env` — check pgAdmin |

---

## 📋 Demo Credentials (after seed_data)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@university.edu | Admin@123 |
| Teacher | teacher@university.edu | Teacher@123 |
| Student | student@university.edu | Student@123 |
