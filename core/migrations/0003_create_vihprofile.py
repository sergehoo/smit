from django.db import migrations, models
import django.db.models.deletion
import django.core.validators

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VIHProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code_vih", models.CharField(db_index=True, max_length=100, unique=True)),
                ("site_code", models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ("numero_dossier_vih", models.CharField(blank=True, db_index=True, max_length=100, null=True)),
                ("status", models.CharField(choices=[...], db_index=True, default="active", max_length=20)),
                ("date_diagnostic", models.DateField(blank=True, db_index=True, null=True)),
                ("date_enrolement", models.DateField(blank=True, db_index=True, null=True)),
                ("date_debut_arv", models.DateField(blank=True, db_index=True, null=True)),
                ("date_derniere_visite", models.DateField(blank=True, db_index=True, null=True)),
                ("date_prochaine_visite", models.DateField(blank=True, db_index=True, null=True)),
                ("vih_type", models.CharField(choices=[...], db_index=True, default="unknown", max_length=10)),
                ("oms_stage", models.IntegerField(blank=True, choices=[...], db_index=True, null=True)),
                ("cd4_baseline", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("charge_virale_baseline", models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ("date_bilan_baseline", models.DateField(blank=True, null=True)),
                ("tb_coinfection", models.CharField(choices=[...], default="unknown", max_length=10)),
                ("hbv_coinfection", models.CharField(choices=[...], default="unknown", max_length=10)),
                ("hcv_coinfection", models.CharField(choices=[...], default="unknown", max_length=10)),
                ("regimen_code", models.CharField(blank=True, db_index=True, help_text="Code schéma ARV...", max_length=80, null=True)),
                ("ligne_traitement", models.CharField(choices=[...], db_index=True, default="unknown", max_length=10)),
                ("adherence_estimee", models.CharField(choices=[...], default="unknown", max_length=10)),
                ("grossesse_en_cours", models.BooleanField(default=False)),
                ("allaitement", models.BooleanField(default=False)),
                ("provenance", models.CharField(blank=True, max_length=255, null=True)),
                ("motif_transfert", models.CharField(blank=True, max_length=255, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("extra", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("patient", models.OneToOneField(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="vih_profile", to="core.patient")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vih_profiles_created", to="core.employee")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vih_profiles_updated", to="core.employee")),
            ],
            options={
                "verbose_name": "Dossier VIH",
                "verbose_name_plural": "Dossiers VIH",
            },
        ),
        migrations.AddIndex(
            model_name="vihprofile",
            index=models.Index(fields=["status", "date_prochaine_visite"], name="core_vihpr_status_..."),
        ),
        migrations.AddIndex(
            model_name="vihprofile",
            index=models.Index(fields=["site_code", "status"], name="core_vihpr_site_co..."),
        ),
        migrations.AddIndex(
            model_name="vihprofile",
            index=models.Index(fields=["date_debut_arv"], name="core_vihpr_date_de..."),
        ),
    ]