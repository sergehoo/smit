# Generated by Django 4.2.14 on 2025-02-06 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smit', '0005_historicalparaclinicalexam_result_value_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalparaclinicalexam',
            name='iteration',
            field=models.PositiveIntegerField(default=1, help_text='Nombre de fois où cet examen a été réalisé.'),
        ),
        migrations.AddField(
            model_name='paraclinicalexam',
            name='iteration',
            field=models.PositiveIntegerField(default=1, help_text='Nombre de fois où cet examen a été réalisé.'),
        ),
    ]
