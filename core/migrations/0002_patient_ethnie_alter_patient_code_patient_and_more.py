# Generated by Django 4.2.14 on 2024-10-23 12:05

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='ethnie',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='code_patient',
            field=models.CharField(default=core.models.get_incremental_code, max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='code_vih',
            field=models.CharField(default=core.models.get_random_code, max_length=100, unique=True),
        ),
    ]