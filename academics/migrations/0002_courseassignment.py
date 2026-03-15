from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0001_initial'),
        ('accounts', '0002_profiles'),  # TeacherProfile is defined here
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.IntegerField(choices=[(1, '1st Semester'), (2, '2nd Semester'), (3, '3rd Semester'), (4, '4th Semester'), (5, '5th Semester'), (6, '6th Semester'), (7, '7th Semester'), (8, '8th Semester')])),
                ('year', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(2000), django.core.validators.MaxValueValidator(2100)])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='academics.course')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_assignments', to='accounts.teacherprofile')),
            ],
            options={
                'ordering': ['-year', 'semester'],
                'unique_together': {('course', 'semester', 'year')},
                'indexes': [models.Index(fields=['semester', 'year'], name='academics_ca_sem_year_idx')],
            },
        ),
    ]
