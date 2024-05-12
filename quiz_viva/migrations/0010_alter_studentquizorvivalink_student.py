# Generated by Django 5.0.1 on 2024-05-12 13:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin", "0008_coursefacultylink_unique_course_faculty_link"),
        ("quiz_viva", "0009_remove_quizorviva_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="studentquizorvivalink",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="admin.student"
            ),
        ),
    ]
