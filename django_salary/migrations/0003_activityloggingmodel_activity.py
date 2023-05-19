# Generated by Django 4.2 on 2023-05-19 09:28

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_salary', '0002_activityloggingmodel_remove_loggingmodel_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityloggingmodel',
            name='activity',
            field=models.CharField(blank=True, db_index=True, default='', error_messages=False, help_text='<small class="text-muted">CharField [0, 100]</small><hr><br>', max_length=100, null=True, validators=[django.core.validators.MinLengthValidator(0), django.core.validators.MaxLengthValidator(100)], verbose_name='Действие'),
        ),
    ]