# Generated by Django 5.0.1 on 2024-05-11 07:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz_viva", "0003_answer_is_correct"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizorviva",
            name="qbank",
            field=models.ForeignKey(
                default="124",
                on_delete=django.db.models.deletion.CASCADE,
                to="quiz_viva.questionbank",
            ),
            preserve_default=False,
        ),
    ]
