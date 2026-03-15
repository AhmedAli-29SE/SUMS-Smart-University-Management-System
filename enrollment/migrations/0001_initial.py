from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_profiles'),
        ('academics', '0002_courseassignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('course_assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='academics.courseassignment')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='accounts.studentprofile')),
            ],
            options={
                'ordering': ['-enrolled_at'],
                'unique_together': {('student', 'course_assignment')},
                'indexes': [models.Index(fields=['student', 'course_assignment'], name='enrollment_stu_ca_idx')],
            },
        ),
    ]
