# Generated by Django 4.2.14 on 2024-08-14 00:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smit', '0002_testrapidevih_consultation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testrapidevih',
            name='consultation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tests_for_consultation_vih', to='smit.consultation'),
        ),
    ]