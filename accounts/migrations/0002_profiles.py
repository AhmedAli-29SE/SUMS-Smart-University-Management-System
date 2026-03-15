from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('academics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(max_length=20, unique=True)),
                ('designation', models.CharField(choices=[('LECTURER', 'Lecturer'), ('ASST_PROF', 'Assistant Professor'), ('ASSOC_PROF', 'Associate Professor'), ('PROFESSOR', 'Professor'), ('HOD', 'Head of Department')], default='LECTURER', max_length=15)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('qualification', models.CharField(blank=True, max_length=100)),
                ('joining_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teachers', to='academics.department')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_profile', to='accounts.customuser')),
            ],
            options={
                'verbose_name': 'Teacher Profile',
                'verbose_name_plural': 'Teacher Profiles',
                'indexes': [models.Index(fields=['employee_id'], name='accounts_tp_empid_idx')],
            },
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_number', models.CharField(max_length=20, unique=True)),
                ('semester', models.PositiveSmallIntegerField(default=1)),
                ('session', models.CharField(help_text='e.g. 2023-2027', max_length=20)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='students/')),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='academics.department')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to='accounts.customuser')),
            ],
            options={
                'verbose_name': 'Student Profile',
                'verbose_name_plural': 'Student Profiles',
                'indexes': [models.Index(fields=['registration_number'], name='accounts_sp_regnum_idx')],
            },
        ),
    ]
