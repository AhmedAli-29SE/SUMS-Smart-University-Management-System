-- Run this in pgAdmin Query Tool to reset migration history
-- This lets you re-run migrate on a database that had previous migrations

-- Step 1: Drop all app tables (safest: drop & recreate DB)
-- OR just clear migration history:

DELETE FROM django_migrations 
WHERE app IN ('accounts', 'academics', 'enrollment', 'attendance', 'results');

-- After running this, go back to PowerShell and run:
-- python manage.py migrate
-- python manage.py seed_data
