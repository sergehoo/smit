# Generated by Django 4.2.14 on 2024-11-01 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0003_medicament_dosage_form'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicament',
            name='unitdosage',
            field=models.CharField(blank=True, choices=[('mg', 'Milligramme (mg)'), ('g', 'Gramme (g)'), ('ml', 'Millilitre (ml)'), ('L', 'Litre (L)'), ('mcg', 'Microgramme (mcg)'), ('UI', 'Unité Internationale (UI)'), ('meq', 'Milliequivalent (mEq)'), ('µL', 'Microlitre (µL)'), ('cm³', 'Centimètre Cube (cm³)'), ('mL/kg', 'Millilitre par kilogramme (mL/kg)'), ('mg/m²', 'Milligramme par mètre carré (mg/m²)'), ('mg/kg', 'Milligramme par kilogramme (mg/kg)'), ('g/L', 'Gramme par litre (g/L)')], help_text='Ex: 500mg, 20mg/ml', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='medicament',
            name='dosage',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
