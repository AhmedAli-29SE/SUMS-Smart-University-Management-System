from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0002_profiles'),
        ('enrollment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('LATE', 'Late'), ('EXCUSED', 'Excused')], default='PRESENT', max_length=10)),
                ('remarks', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='enrollment.enrollment')),
                ('marked_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_marked', to='accounts.customuser')),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('enrollment', 'date')},
                'indexes': [
                    models.Index(fields=['enrollment', 'date'], name='attendance_enr_date_idx'),
                    models.Index(fields=['date'], name='attendance_date_idx'),
                ],
            },
        ),
    ]
