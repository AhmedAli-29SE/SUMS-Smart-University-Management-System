from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_profiles'),
        ('enrollment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('midterm_marks', models.DecimalField(blank=True, decimal_places=2, help_text='Out of 30', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(30)])),
                ('final_marks', models.DecimalField(blank=True, decimal_places=2, help_text='Out of 50', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(50)])),
                ('assignment_marks', models.DecimalField(blank=True, decimal_places=2, help_text='Out of 20', max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(20)])),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('grade', models.CharField(blank=True, choices=[('A+', 'A+'), ('A', 'A'), ('A-', 'A-'), ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'), ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'), ('D', 'D'), ('F', 'F (Fail)')], max_length=3)),
                ('gpa_points', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('enrollment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='enrollment.enrollment')),
                ('entered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='results_entered', to='accounts.customuser')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['enrollment'], name='results_enr_idx')],
            },
        ),
    ]
