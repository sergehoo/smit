# Generated by Django 4.2.14 on 2025-01-20 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_maladie_code_cim_patient_cmu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maladie',
            name='code_cim',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
