# Generated by Django 4.2.14 on 2025-02-03 13:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pharmacy', '0001_initial'),
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalemployee',
            name='pharmacie',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='pharmacy.pharmacy', verbose_name='Pharmacie'),
        ),
        migrations.AddField(
            model_name='historicalemployee',
            name='user',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='healthregion',
            name='poles',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.polesregionaux'),
        ),
        migrations.AddField(
            model_name='employee',
            name='departement',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.service', verbose_name='service'),
        ),
        migrations.AddField(
            model_name='employee',
            name='pharmacie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pharmacy.pharmacy', verbose_name='Pharmacie'),
        ),
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='districtsanitaire',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.healthregion'),
        ),
        migrations.AddField(
            model_name='cascontact',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='case_contacts', to='core.patient', verbose_name='Patient'),
        ),
        migrations.AlterUniqueTogether(
            name='patientuserobjectpermission',
            unique_together={('user', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='patientgroupobjectpermission',
            unique_together={('group', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='cascontact',
            unique_together={('patient', 'contact_person')},
        ),
    ]
