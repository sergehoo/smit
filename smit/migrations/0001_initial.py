# Generated by Django 4.2.14 on 2024-10-22 11:37

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import simple_history.models
import smit.models
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('schedule', '0014_use_autofields_for_pk'),
        ('pharmacy', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Allergies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(blank=True, max_length=255, null=True)),
                ('descriptif', models.CharField(blank=True, max_length=255, null=True)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='Analyse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name="Nom de l'analyse")),
                ('nbrb', models.PositiveIntegerField(blank=True, default=100, null=True)),
                ('tarif_base', models.PositiveIntegerField(blank=True, default=100, null=True)),
                ('tarif_public', models.PositiveIntegerField(blank=True, null=True)),
                ('tarif_mutuelle', models.PositiveIntegerField(blank=True, null=True)),
                ('forfait_assurance', models.PositiveIntegerField(blank=True, null=True)),
                ('forfait_societe', models.PositiveIntegerField(blank=True, null=True)),
                ('lanema', models.PositiveIntegerField(blank=True, null=True)),
                ('analysis_description', tinymce.models.HTMLField(blank=True, null=True)),
                ('analysis_method', models.CharField(blank=True, max_length=50, null=True)),
                ('delai_analyse', models.PositiveIntegerField(blank=True, null=True)),
                ('result', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AntecedentsMedicaux',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(blank=True, max_length=255, null=True)),
                ('descriptif', models.CharField(blank=True, max_length=255, null=True)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('reason', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('calendar', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedule.calendar')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments_creator', to='core.employee')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.employee')),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schedule.event')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
                ('service', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.service')),
            ],
        ),
        migrations.CreateModel(
            name='BoxHospitalisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capacite', models.PositiveIntegerField(default=1)),
                ('nom', models.CharField(max_length=100)),
                ('occuper', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Constante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tension_systolique', models.IntegerField(blank=True, null=True, verbose_name='Tension artérielle systolique')),
                ('tension_diastolique', models.IntegerField(blank=True, null=True, verbose_name='Tension artérielle diastolique')),
                ('frequence_cardiaque', models.IntegerField(blank=True, null=True, verbose_name='Fréquence cardiaque')),
                ('frequence_respiratoire', models.IntegerField(blank=True, null=True, verbose_name='Fréquence respiratoire')),
                ('temperature', models.FloatField(blank=True, null=True, verbose_name='Température')),
                ('saturation_oxygene', models.IntegerField(blank=True, null=True, verbose_name='Saturation en oxygène')),
                ('glycemie', models.FloatField(blank=True, null=True, verbose_name='Glycémie')),
                ('poids', models.FloatField(blank=True, null=True, verbose_name='Poids')),
                ('taille', models.FloatField(blank=True, null=True, verbose_name='Taille')),
                ('pouls', models.FloatField(blank=True, null=True, verbose_name='Pouls')),
                ('imc', models.FloatField(blank=True, editable=False, null=True, verbose_name='IMC')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='constantes_creator', to='core.employee')),
            ],
            options={
                'verbose_name': 'Constante',
                'verbose_name_plural': 'Constantes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Consultation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numeros', models.CharField(default=smit.models.consult_number, max_length=300, unique=True)),
                ('consultation_date', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('reason', models.TextField(blank=True, null=True)),
                ('diagnosis', tinymce.models.HTMLField()),
                ('commentaires', tinymce.models.HTMLField()),
                ('status', models.CharField(blank=True, choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=50, null=True)),
                ('hospitalised', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('requested_at', models.DateTimeField(blank=True, null=True)),
                ('motifrejet', models.CharField(blank=True, max_length=300, null=True)),
                ('validated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('activite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='acti_consultations', to='core.servicesubactivity')),
                ('allergies', models.ManyToManyField(blank=True, related_name='patientallergies', to='smit.allergies')),
                ('antecedentsMedicaux', models.ManyToManyField(blank=True, related_name='patientantecedents', to='smit.antecedentsmedicaux')),
                ('constante', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patientconstantes', to='smit.constante')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultation_creator', to='core.employee')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultations', to='core.employee')),
            ],
        ),
        migrations.CreateModel(
            name='EtapeProtocole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('date_fin', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FicheSuiviClinique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_consultation', models.DateField(help_text='Date de la consultation.')),
                ('heure_consultation', models.TimeField(blank=True, help_text='Heure de la consultation.', null=True)),
                ('observations_cliniques', models.TextField(blank=True, help_text='Observations cliniques du médecin.', null=True)),
                ('poids', models.DecimalField(blank=True, decimal_places=2, help_text='Poids du patient en kg.', max_digits=5, null=True)),
                ('taille', models.DecimalField(blank=True, decimal_places=2, help_text='Taille du patient en cm.', max_digits=5, null=True)),
                ('pression_arterielle', models.CharField(blank=True, help_text='Exemple : 120/80 mmHg', max_length=20, null=True)),
                ('temperature', models.DecimalField(blank=True, decimal_places=1, help_text='Température corporelle en °C.', max_digits=4, null=True)),
                ('recommandations', models.TextField(blank=True, help_text='Recommandations du médecin pour le patient.', null=True)),
                ('prochaine_consultation', models.DateField(blank=True, help_text='Date de la prochaine consultation prévue.', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('medecin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fichemedecinsuivi', to='core.employee')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consultations', to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='Hospitalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admission_date', models.DateTimeField()),
                ('discharge_date', models.DateTimeField(blank=True, null=True)),
                ('discharge_reason', models.CharField(blank=True, max_length=700, null=True)),
                ('room', models.CharField(max_length=500)),
                ('reason_for_admission', models.TextField()),
                ('status', models.CharField(blank=True, choices=[('Admis', 'Admis'), ('Sorti', 'Sorti'), ('Gueris-EXEA', 'Gueris-EXEA'), ('Transféré-TRANSF', 'Transféré-TRANSF'), ('SCAM', 'SCAM'), ('EVADE', 'EVADE'), ('DCD', 'DCD'), ('Sous observation', 'Sous observation'), ('Sous traitement', 'Sous traitement'), ('Chirurgie programmée', 'Chirurgie programmée'), ('En chirurgie', 'En chirurgie'), ('Récupération post-opératoire', 'Récupération post-opératoire'), ('USI', 'Unité de soins intensifs (USI)'), ('Urgence', 'Urgence'), ('Consultation externe', 'Consultation externe'), ('Réhabilitation', 'Réhabilitation'), ('En attente de diagnostic', 'En attente de diagnostic'), ('Traitement en cours', 'Traitement en cours'), ('Suivi programmé', 'Suivi programmé'), ('Consultation', 'Consultation'), ('Sortie en attente', 'Sortie en attente'), ('Isolement', 'Isolement'), ('Ambulantoire', 'Ambulantoire'), ('Aucun', 'Aucun')], max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('activite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='acti_hospitalied', to='core.servicesubactivity')),
            ],
        ),
        migrations.CreateModel(
            name='MaladieOpportuniste',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TypeAntecedent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='UniteHospitalisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('capacite', models.PositiveIntegerField(default=1)),
                ('type', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='WaitingRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arrival_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('Waiting', 'Waiting'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('medecin', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waiting_rooms', to='core.employee')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
                ('service', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='waiting_rooms', to='core.service')),
            ],
        ),
        migrations.CreateModel(
            name='TraitementARV',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('regime', models.CharField(help_text='Schéma thérapeutique ARV.', max_length=255)),
                ('date_debut', models.DateField(help_text='Date de début du traitement ARV.')),
                ('date_fin', models.DateField(blank=True, help_text='Date de fin du traitement si applicable.', null=True)),
                ('adherence', models.CharField(choices=[('Bonne', 'Bonne'), ('Moyenne', 'Moyenne'), ('Faible', 'Faible')], default='Bonne', help_text="Niveau d'adhérence au traitement.", max_length=20)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='traitements_arv', to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='TestRapideVIH',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_test', models.DateTimeField(auto_now_add=True)),
                ('resultat', models.CharField(choices=[('POSITIF', 'Positif'), ('NEGATIF', 'Négatif')], max_length=20)),
                ('laboratoire', models.CharField(max_length=100)),
                ('test_type', models.CharField(blank=True, choices=[], max_length=100, null=True)),
                ('commentaire', models.TextField(blank=True, null=True)),
                ('consultation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tests_for_consultation_vih', to='smit.consultation')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tests_rapides_vih', to='core.patient')),
            ],
            options={
                'verbose_name': 'Test Rapide VIH',
                'verbose_name_plural': 'Tests Rapides VIH',
            },
        ),
        migrations.CreateModel(
            name='Symptomes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(blank=True, max_length=255, null=True)),
                ('descriptif', models.CharField(blank=True, max_length=255, null=True)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='Suivi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suiviactivitepat', to='core.servicesubactivity')),
                ('fichesuivie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suivisfiche', to='smit.fichesuiviclinique')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suivimedecin', to='core.patient')),
                ('rdvconsult', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suivierdvconsult', to='smit.appointment')),
                ('rdvpharmacie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suivierdvpharma', to='pharmacy.rendezvous')),
                ('services', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servicesuivipat', to='core.service')),
                ('traitement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suivispatient', to='smit.traitementarv')),
            ],
        ),
        migrations.CreateModel(
            name='SigneFonctionnel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
                ('valeure', models.CharField(choices=[('oui', 'oui'), ('non', 'non')], max_length=255)),
                ('hospitalisation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signefonctionnels', to='smit.hospitalization')),
            ],
        ),
        migrations.CreateModel(
            name='Protocole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('duree', models.PositiveIntegerField(blank=True, null=True)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('molecules', models.ManyToManyField(to='pharmacy.molecule')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='protocoles', to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('prescribed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Dispensed', 'Dispensed'), ('Cancelled', 'Cancelled')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prescription_creator', to='core.employee')),
                ('doctor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prescriptions', to='core.employee')),
                ('medication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy.medicament')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='LitHospitalisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(default='lit', max_length=100)),
                ('occuper', models.BooleanField(default=False)),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lits', to='smit.boxhospitalisation')),
                ('occupant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.patient')),
                ('reserved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.employee')),
            ],
        ),
        migrations.CreateModel(
            name='IndicateurSubjectif',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('bien_etre', models.IntegerField(blank=True, choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)], null=True)),
                ('hospitalisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicateurs_subjectifs', to='smit.hospitalization')),
            ],
        ),
        migrations.CreateModel(
            name='IndicateurFonctionnel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('mobilite', models.CharField(blank=True, choices=[('indépendant', 'Indépendant'), ('assisté', 'Assisté'), ('immobile', 'Immobile')], max_length=50, null=True)),
                ('conscience', models.CharField(blank=True, choices=[('alerte', 'Alerte'), ('somnolent', 'Somnolent'), ('inconscient', 'Inconscient')], max_length=50, null=True)),
                ('debit_urinaire', models.DecimalField(blank=True, decimal_places=2, help_text='Litres', max_digits=5, null=True)),
                ('hospitalisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicateurs_fonctionnels', to='smit.hospitalization')),
            ],
        ),
        migrations.CreateModel(
            name='IndicateurBiologique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('globules_blancs', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('hemoglobine', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('plaquettes', models.IntegerField(blank=True, null=True)),
                ('crp', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('glucose_sanguin', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('hospitalisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicateurs_biologiques', to='smit.hospitalization')),
            ],
        ),
        migrations.AddField(
            model_name='hospitalization',
            name='bed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='smit.lithospitalisation'),
        ),
        migrations.AddField(
            model_name='hospitalization',
            name='doctor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hospitaliza_doctor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='hospitalization',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospitalized', to='core.patient'),
        ),
        migrations.CreateModel(
            name='HistoricalAnalyse',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name="Nom de l'analyse")),
                ('nbrb', models.PositiveIntegerField(blank=True, default=100, null=True)),
                ('tarif_base', models.PositiveIntegerField(blank=True, default=100, null=True)),
                ('tarif_public', models.PositiveIntegerField(blank=True, null=True)),
                ('tarif_mutuelle', models.PositiveIntegerField(blank=True, null=True)),
                ('forfait_assurance', models.PositiveIntegerField(blank=True, null=True)),
                ('forfait_societe', models.PositiveIntegerField(blank=True, null=True)),
                ('lanema', models.PositiveIntegerField(blank=True, null=True)),
                ('analysis_description', tinymce.models.HTMLField(blank=True, null=True)),
                ('analysis_method', models.CharField(blank=True, max_length=50, null=True)),
                ('delai_analyse', models.PositiveIntegerField(blank=True, null=True)),
                ('result', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical analyse',
                'verbose_name_plural': 'historical analyses',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Examen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_number', models.CharField(default=smit.models.request_number, max_length=100, unique=True)),
                ('number', models.CharField(blank=True, max_length=300, null=True)),
                ('delivered_by', models.CharField(blank=True, max_length=300, null=True)),
                ('delivered_contact', models.CharField(blank=True, max_length=300, null=True)),
                ('delivered_services', models.CharField(blank=True, max_length=300, null=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('accepted', models.BooleanField(blank=True, default=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('analyses', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='smit.analyse', verbose_name="Type d'analyse")),
                ('consultation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='examen_for_consultation', to='smit.consultation')),
                ('patients_requested', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient', verbose_name='patients')),
            ],
        ),
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_evaluation', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('etat_patient', models.CharField(blank=True, max_length=255, null=True)),
                ('etape', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='smit.etapeprotocole')),
            ],
        ),
        migrations.AddField(
            model_name='etapeprotocole',
            name='protocole',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='etapes', to='smit.protocole'),
        ),
        migrations.CreateModel(
            name='EnqueteVih',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prophylaxie_antiretrovirale', models.BooleanField(default=False)),
                ('prophylaxie_type', models.CharField(blank=True, max_length=255, null=True)),
                ('traitement_antiretrovirale', models.BooleanField(default=False)),
                ('traitement_type', models.CharField(blank=True, max_length=255, null=True)),
                ('dernier_regime_antiretrovirale', models.BooleanField(default=False)),
                ('dernier_regime_antiretrovirale_type', models.CharField(blank=True, max_length=255, null=True)),
                ('traitement_prophylactique_cotrimoxazole', models.BooleanField(default=False)),
                ('evolutif_cdc_1993', models.CharField(blank=True, choices=[('Adulte Stade A', 'Adulte Stade A'), ('Adulte Stade B', 'Adulte Stade B'), ('Adulte Stade C', 'Adulte Stade C'), ('Enfant Stade N', 'Enfant Stade N'), ('Enfant Stade A', 'Enfant Stade A'), ('Enfant Stade B', 'Enfant Stade B'), ('Enfant Stade C', 'Enfant Stade C')], max_length=255, null=True)),
                ('sous_traitement', models.BooleanField(default=False)),
                ('score_karnofsky', models.IntegerField(blank=True, null=True)),
                ('descriptif', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('antecedents', models.ManyToManyField(related_name='antecedents_vih', to='smit.maladieopportuniste')),
                ('consultation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='enqueteconsultation', to='smit.consultation')),
                ('infection_opportuniste', models.ManyToManyField(related_name='infection_opportuniste', to='smit.maladieopportuniste')),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='enquetevihs', to='core.patient')),
            ],
        ),
        migrations.CreateModel(
            name='Emergency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arrival_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('Waiting', 'Waiting'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved'), ('Referred', 'Referred')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='emergencies', to='core.employee')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient')),
            ],
        ),
        migrations.AddField(
            model_name='consultation',
            name='examens',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patientexamens', to='smit.examen'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.patient'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='services',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultations', to='core.service'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='suivi',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='suivi', to='core.service'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='symptomes',
            field=models.ManyToManyField(blank=True, related_name='patientsymptomes', to='smit.symptomes'),
        ),
        migrations.AddField(
            model_name='constante',
            name='hospitalisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hospiconstantes', to='smit.hospitalization'),
        ),
        migrations.AddField(
            model_name='constante',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='constantes', to='core.patient'),
        ),
        migrations.CreateModel(
            name='ChambreHospitalisation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('unite', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chambres', to='smit.unitehospitalisation')),
            ],
        ),
        migrations.AddField(
            model_name='boxhospitalisation',
            name='chambre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boxes', to='smit.chambrehospitalisation'),
        ),
        migrations.AddField(
            model_name='boxhospitalisation',
            name='occupant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.patient'),
        ),
        migrations.AddField(
            model_name='antecedentsmedicaux',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='smit.typeantecedent'),
        ),
    ]