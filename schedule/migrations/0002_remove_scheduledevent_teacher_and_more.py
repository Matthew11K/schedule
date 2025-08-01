# Generated by Django 5.1.5 on 2025-07-17 14:58

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_level_options_alter_subject_options_and_more"),
        ("groups", "0002_remove_student_group_student_groups_lesson_and_more"),
        ("schedule", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scheduledevent",
            name="teacher",
        ),
        migrations.AddField(
            model_name="scheduledevent",
            name="academic_hours",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Количество академических часов события",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(10),
                ],
                verbose_name="Академические часы",
            ),
        ),
        migrations.AddField(
            model_name="scheduledevent",
            name="group",
            field=models.ForeignKey(
                default=1,
                help_text="Группа, участвующая в событии",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="scheduled_events",
                to="groups.group",
                verbose_name="Группа",
            ),
        ),
        migrations.AddField(
            model_name="scheduledevent",
            name="teachers",
            field=models.ManyToManyField(
                help_text="Преподаватели, ведущие событие",
                related_name="scheduled_events",
                to="core.teacher",
                verbose_name="Преподаватели",
            ),
        ),
    ]
