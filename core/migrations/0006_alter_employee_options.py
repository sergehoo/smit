# Generated by Django 4.2.14 on 2024-11-20 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_patient_code_patient'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employee',
            options={'permissions': (('can_edit_employee', 'Can edit employee'), ('can_create_employee', 'Can create employee'), ('can_view_salary', 'can view salary'), ('can_view_employee', 'can view employee'))},
        ),
    ]