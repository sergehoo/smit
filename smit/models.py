import datetime
import io
import random
import unicodedata
import uuid

from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.db.models import Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now
from django_countries.fields import CountryField
from schedule.models import Calendar, Event
from simple_history.models import HistoricalRecords
from tinymce.models import HTMLField

from core.models import Patient, Service, Employee, ServiceSubActivity, Patient_statut_choices
from pharmacy.models import Medicament, Molecule, RendezVous

# from pharmacy.models import Medication
RAPID_HIV_TEST_TYPES = [
    ('Determine HIV-1/2', 'Determine HIV-1/2'),
    ('Uni-Gold HIV', 'Uni-Gold HIV'),
    ('SD Bioline HIV-1/2', 'SD Bioline HIV-1/2'),
    ('OraQuick HIV', 'OraQuick HIV'),
    ('INSTI HIV-1/HIV-2', 'INSTI HIV-1/HIV-2'),
    ('Alere HIV Combo, First Response HIV 1-2-0 Card Test', 'Alere HIV Combo, First Response HIV 1-2-0 Card Test'),
    ('Chembio HIV 1/2 STAT-PAK® Assay', 'Chembio HIV 1/2 STAT-PAK® Assay'),
    ('OraQuick HIV 1/2', 'OraQuick HIV 1/2'),
    ('Alere Determine HIV-1/2 Ag/Ab Combo', 'Alere Determine HIV-1/2 Ag/Ab Combo'),
    ('Geenius™ HIV 1/2 Confirmatory Assay', 'Geenius™ HIV 1/2 Confirmatory Assay'),
    # Ajoutez d'autres types si nécessaire
]

antecedents_type = [
    ('Antécédents médicaux personnels', 'Antécédents médicaux personnels'),
    ('Antécédents familiaux', 'Antécédents familiaux'),
    ('Antécédents chirurgicaux', 'Antécédents chirurgicaux'),
    ('Antécédents gynécologiques et obstétricaux', 'Antécédents gynécologiques et obstétricaux'),
    ('Antécédents médicamenteux', 'Antécédents médicamenteux'),
    ('Antécédents psychologiques', 'Antécédents psychologiques'),
    ('Antécédents sociaux', 'Antécédents sociaux'),
    ('Antécédents obstétricaux', 'Antécédents obstétricaux')
]

POSOLOGY_CHOICES = [
    ('Une fois par jour', 'Une fois par jour'),
    ('Deux fois par jour', 'Deux fois par jour'),
    ('Trois fois par jour', 'Trois fois par jour'),
    ('Quatre fois par jour', 'Quatre fois par jour'),
    ('Toutes les 4 heures', 'Toutes les 4 heures'),
    ('Toutes les 6 heures', 'Toutes les 6 heures'),
    ('Toutes les 8 heures', 'Toutes les 8 heures'),
    ('Si besoin', 'Si besoin'),
    ('Avant les repas', 'Avant les repas'),
    ('Après les repas', 'Après les repas'),
    ('Au coucher', 'Au coucher'),
    ('Une fois par semaine', 'Une fois par semaine'),
    ('Deux fois par semaine', 'Deux fois par semaine'),
    ('Un jour sur deux', 'Un jour sur deux'),
]

DELAY_CHOICES = [
    ('1', '1 jour'),
    ('2', '2 jours'),
    ('3', '3 jours'),
    ('4', '4 jours'),
    ('5', '5 jours'),
    ('7', '1 semaine'),
    ('14', '2 semaines'),
    ('21', '3 semaines'),
    ('30', '1 mois'),
]

FROM_CHOICES = [
    ('1', '1 heure'),
    ('2', '2 heures'),
    ('3', '3 heures'),
    ('4', '4 heures'),
    ('6', '6 heures'),
    ('8', '8 heures'),
    ('12', '12 heures'),
    ('24', '24 heures'),
    ('48', '48 heures'),
    ('72', '72 heures'),
]


def request_number():
    WordStack = ['S', 'M', 'I', 'T', 'C', '', 'I']
    random_str = random.choice(WordStack)
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    traking = (random_str + str(random.randrange(0, 9999, 1)) + current_date)
    return traking


def consult_number():
    WordStack = ['S', 'M', 'I', 'T', 'C', '', 'I']
    random_str = random.choice(WordStack)
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    traking = (random_str + str(random.randrange(0, 9999, 1)) + current_date)
    return traking


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    doctor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ])
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='appointments_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.date} {self.time}"


class Emergency(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='emergencies')
    arrival_time = models.DateTimeField(default=timezone.now)
    reason = models.TextField()
    status = models.CharField(max_length=50, choices=[
        ('Waiting', 'Waiting'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Referred', 'Referred')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.arrival_time}"


class Protocole(models.Model):
    nom = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    duree = models.PositiveIntegerField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    molecules = models.ManyToManyField(Molecule)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="protocoles")

    def __str__(self):
        return self.nom


class EtapeProtocole(models.Model):
    protocole = models.ForeignKey(Protocole, on_delete=models.CASCADE, related_name="etapes")
    nom = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.protocole.nom} - {self.nom}"


class Evaluation(models.Model):
    etape = models.ForeignKey(EtapeProtocole, on_delete=models.CASCADE, related_name="evaluations", null=True,
                              blank=True)
    date_evaluation = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    etat_patient = models.CharField(max_length=255, null=True,
                                    blank=True)  # Ex. 'Amélioration', 'Stable', 'Dégradation'

    def __str__(self):
        return f"Évaluation de {self.etape.protocole.patient.nom} le {self.date_evaluation}"


class Symptomes(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=255, null=True, blank=True)
    descriptif = models.CharField(max_length=255, null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Symptomes for {self.patient.nom} on {self.created_at}"


class MaladieOpportuniste(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom


class EnqueteVih(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='enquetevihs', null=True, blank=True)
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='enqueteconsultation',
                                     null=True, blank=True)
    antecedents = models.ManyToManyField(MaladieOpportuniste, related_name='antecedents_vih')
    prophylaxie_antiretrovirale = models.BooleanField(default=False)
    prophylaxie_type = models.CharField(max_length=255, null=True, blank=True)
    traitement_antiretrovirale = models.BooleanField(default=False)
    traitement_type = models.CharField(max_length=255, null=True, blank=True)
    dernier_regime_antiretrovirale = models.BooleanField(default=False)
    dernier_regime_antiretrovirale_type = models.CharField(max_length=255, null=True, blank=True)

    traitement_prophylactique_cotrimoxazole = models.BooleanField(default=False)

    evolutif_cdc_1993 = models.CharField(choices=[('Adulte Stade A', 'Adulte Stade A'),
                                                  ('Adulte Stade B', 'Adulte Stade B'),
                                                  ('Adulte Stade C', 'Adulte Stade C'),

                                                  ('Enfant Stade N', 'Enfant Stade N'),
                                                  ('Enfant Stade A', 'Enfant Stade A'),
                                                  ('Enfant Stade B', 'Enfant Stade B'),
                                                  ('Enfant Stade C', 'Enfant Stade C'),
                                                  ], max_length=255,
                                         null=True, blank=True)

    infection_opportuniste = models.ManyToManyField(MaladieOpportuniste, related_name='infection_opportuniste')
    sous_traitement = models.BooleanField(default=False)

    score_karnofsky = models.IntegerField(null=True, blank=True)
    descriptif = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Antecedents Medicaux for {self.patient.nom} on {self.created_at}"


class TypeAntecedent(models.Model):
    nom = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nom


class AntecedentsMedicaux(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    nom = models.CharField(max_length=255, null=True, blank=True)
    type = models.ForeignKey(TypeAntecedent, on_delete=models.SET_NULL, null=True, blank=True)
    descriptif = models.CharField(max_length=255, null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Antecedents Medicaux for {self.patient.nom} on {self.created_at}"


class Allergies(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    titre = models.CharField(max_length=255, null=True, blank=True)
    descriptif = models.CharField(max_length=255, null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Allergies for {self.patient.nom} on {self.created_at}"


class Analyse(models.Model):
    # code = models.CharField(default=analyse_number, max_length=100, unique=True)
    name = models.CharField(max_length=255, verbose_name='Nom de l\'analyse', unique=True)
    # category = models.ForeignKey('CathegorieAnalyse', null=True, blank=True, on_delete=models.CASCADE)
    nbrb = models.PositiveIntegerField(null=True, blank=True, default=100)
    tarif_base = models.PositiveIntegerField(null=True, blank=True, default=100)
    tarif_public = models.PositiveIntegerField(null=True, blank=True)
    tarif_mutuelle = models.PositiveIntegerField(null=True, blank=True)
    forfait_assurance = models.PositiveIntegerField(null=True, blank=True)
    forfait_societe = models.PositiveIntegerField(null=True, blank=True)
    lanema = models.PositiveIntegerField(null=True, blank=True)
    analysis_description = HTMLField(null=True, blank=True)
    analysis_method = models.CharField(max_length=50, null=True, blank=True)
    # analysis_equipment = models.ManyToManyField('Equipment', verbose_name='Kit')
    # analysis_reagents = models.ManyToManyField('Reagent', verbose_name='Réactif')
    delai_analyse = models.PositiveIntegerField(null=True, blank=True)
    # laboratoire = models.ForeignKey('Laboratory', blank=True, null=True, on_delete=models.CASCADE)
    result = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    history = HistoricalRecords()

    # def save(self, *args, **kwargs):
    #     # self.age = (date.today() - self.date_naissance) // (timedelta(days=365.2425))
    #
    #     if self.tarif_base:
    #         self.tarif_public = self.tarif_base * self.nbrb.valeur
    #         self.tarif_mutuelle = (self.tarif_public * 50 / 100) + self.tarif_public
    #         self.forfait_assurance = (self.tarif_public * 100 / 100) + self.tarif_public
    #         self.forfait_societe = (self.tarif_public * 80 / 100) + self.tarif_public
    #         self.lanema = (self.tarif_public + 0.2 * self.tarif_public) / 2
    #
    #     super(Analyse, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class Examen(models.Model):
    request_number = models.CharField(default=request_number, max_length=100, unique=True)
    patients_requested = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="patients")
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='examen_for_consultation')
    number = models.CharField(blank=True, null=True, max_length=300)
    delivered_by = models.CharField(blank=True, null=True, max_length=300)
    delivered_contact = models.CharField(blank=True, null=True, max_length=300)
    delivered_services = models.CharField(blank=True, null=True, max_length=300)
    date = models.DateField(blank=True, null=True)
    analyses = models.ForeignKey('Analyse', on_delete=models.CASCADE, blank=True, verbose_name="Type d'analyse")
    accepted = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # history = HistoricalRecords()

    def __str__(self):
        return f"{self.analyses} for {self.patients_requested} on {self.created_at}"


class TestRapideVIH(models.Model):
    RESULTAT_CHOICES = [
        ('POSITIF', 'Positif'),
        ('NEGATIF', 'Négatif'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='tests_rapides_vih')
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, blank=True, null=True,
                                     related_name='tests_for_consultation_vih')
    date_test = models.DateTimeField(auto_now_add=True)
    resultat = models.CharField(max_length=20, choices=RESULTAT_CHOICES)
    laboratoire = models.CharField(max_length=100)
    test_type = models.CharField(max_length=100, choices=[], blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Test {self.resultat} - {self.patient.nom} {self.patient.prenoms} - {self.date_test.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Test Rapide VIH"
        verbose_name_plural = "Tests Rapides VIH"


class Consultation(models.Model):
    numeros = models.CharField(default=consult_number, max_length=300, unique=True)
    activite = models.ForeignKey(ServiceSubActivity, on_delete=models.CASCADE, related_name="acti_consultations",
                                 null=True, blank=True, )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    constante = models.ForeignKey('Constante', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='patientconstantes')
    symptomes = models.ManyToManyField('Symptomes', related_name='patientsymptomes', blank=True)
    antecedentsMedicaux = models.ManyToManyField('AntecedentsMedicaux', blank=True, related_name='patientantecedents')
    examens = models.ForeignKey('Examen', on_delete=models.SET_NULL, blank=True, null=True,
                                related_name='patientexamens')
    allergies = models.ManyToManyField('Allergies', related_name='patientallergies', blank=True)
    services = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True,
                                 related_name='consultations')

    doctor = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True, related_name='consultations')
    consultation_date = models.DateTimeField(default=timezone.now, blank=True)
    reason = models.TextField(blank=True, null=True, )
    diagnosis = HTMLField()
    commentaires = HTMLField()

    suivi = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True, related_name='suivi')
    status = models.CharField(max_length=50, blank=True, null=True,
                              choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'),
                                       ('Cancelled', 'Cancelled'), ])
    hospitalised = models.PositiveIntegerField(default=0, blank=True, null=True, )
    requested_at = models.DateTimeField(blank=True, null=True, )
    motifrejet = models.CharField(max_length=300, blank=True, null=True, )
    validated_at = models.DateTimeField(blank=True, null=True, )
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, blank=True, null=True,
                                   related_name='consultation_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation for {self.patient.nom} on {self.consultation_date}"


class Constante(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="constantes")
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="hospiconstantes",
                                        null=True, blank=True)
    tension_systolique = models.IntegerField(null=True, blank=True, verbose_name="Tension artérielle systolique")
    tension_diastolique = models.IntegerField(null=True, blank=True, verbose_name="Tension artérielle diastolique")
    frequence_cardiaque = models.IntegerField(null=True, blank=True, verbose_name="Fréquence cardiaque")
    frequence_respiratoire = models.IntegerField(null=True, blank=True, verbose_name="Fréquence respiratoire")
    temperature = models.FloatField(null=True, blank=True, verbose_name="Température")
    saturation_oxygene = models.IntegerField(null=True, blank=True, verbose_name="Saturation en oxygène")
    glycemie = models.FloatField(null=True, blank=True, verbose_name="Glycémie")
    poids = models.FloatField(null=True, blank=True, verbose_name="Poids")
    taille = models.FloatField(null=True, blank=True, verbose_name="Taille")
    pouls = models.FloatField(null=True, blank=True, verbose_name="Pouls")
    imc = models.FloatField(null=True, blank=True, verbose_name="IMC", editable=False)
    pb = models.FloatField(null=True, blank=True, verbose_name="Périmètre Braciale")

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='constantes_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def imc_status(self):
        if self.imc < 18.5:
            return 'Maigreur'
        elif self.imc >= 18.5 and self.imc <= 24.9:
            return 'Normal'
        elif self.imc >= 25 and self.imc <= 29.9:
            return 'Surpoids'
        elif self.imc >= 30 and self.imc <= 34.9:
            return 'Obésité modérée'
        elif self.imc >= 35 and self.imc <= 39.9:
            return 'Obésité sévère'
        elif self.imc >= 40:
            return 'Obésité morbide'

    @property
    def tension_status(self):
        if self.tension < 9:
            return 'Hypotension'
        elif self.tension >= 9 and self.tension <= 13:
            return 'Tension normale'
        elif self.tension >= 14 and self.tension <= 16:
            return 'Hypertension modérée'
        elif self.tension >= 17 and self.tension <= 20:
            return 'Hypertension sévère'
        elif self.tension >= 21:
            return 'Hypertension très sévère'

    @property
    def pouls_status(self):
        if self.pouls is None:
            return 'Non mesuré'
        elif self.pouls < 60:
            return 'Bradycardie'
        elif 60 <= self.pouls <= 100:
            return 'Normal'
        elif self.pouls > 100:
            return 'Tachycardie'

    @property
    def temperature_status(self):
        if self.temperature < 36:
            return 'Hypothermie'
        elif self.temperature >= 36 and self.temperature <= 37.5:
            return 'Normal'
        elif self.temperature >= 37.6 and self.temperature <= 38.5:
            return 'Fièvre modérée'
        elif self.temperature >= 38.6 and self.temperature <= 40:
            return 'Fièvre élevée'
        elif self.temperature >= 40.1:
            return 'Hyperthermie'

    def save(self, *args, **kwargs):
        if self.poids and self.taille:
            self.imc = self.poids / (self.taille / 100) ** 2
        super().save(*args, **kwargs)

    @property
    def alerte(self):
        alertes = []

        # Définir les plages normales pour chaque constante vitale
        if self.tension_systolique and not (90 <= self.tension_systolique <= 140):
            alertes.append(f"Tension systolique anormale: {self.tension_systolique} mmHg")

        if self.tension_diastolique and not (60 <= self.tension_diastolique <= 90):
            alertes.append(f"Tension diastolique anormale: {self.tension_diastolique} mmHg")

        if self.frequence_cardiaque and not (60 <= self.frequence_cardiaque <= 100):
            alertes.append(f"Fréquence cardiaque anormale: {self.frequence_cardiaque} bpm")

        if self.frequence_respiratoire and not (12 <= self.frequence_respiratoire <= 20):
            alertes.append(f"Fréquence respiratoire anormale: {self.frequence_respiratoire} respirations/min")

        if self.temperature and not (36.1 <= self.temperature <= 37.8):
            alertes.append(f"Température anormale: {self.temperature} °C")

        if self.saturation_oxygene and not (95 <= self.saturation_oxygene <= 100):
            alertes.append(f"Saturation en oxygène anormale: {self.saturation_oxygene} %")

        if self.glycemie and not (0.7 <= self.glycemie <= 1.1):
            alertes.append(f"Glycémie anormale: {self.glycemie} g/L")

        if self.pouls and not (60 <= self.pouls <= 100):
            alertes.append(f"Pouls anormal: {self.pouls} bpm")

        # Calculer l'IMC si taille et poids sont disponibles
        if self.taille and self.poids:
            self.imc = round(self.poids / (self.taille / 100) ** 2, 2)
            if not (18.5 <= self.imc <= 24.9):
                alertes.append(f"IMC anormal: {self.imc}")

        # Renvoie les alertes si elles existent, sinon un message normal
        return " | ".join(alertes) if alertes else "Toutes les constantes sont dans les normes."

    def __str__(self):
        return f"Constantes pour {self.patient} le {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Constante"
        verbose_name_plural = "Constantes"


class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='prescriptions')
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="hospiprescriptions", null=True, blank=True)
    medication = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    posology = models.CharField(max_length=350, choices=POSOLOGY_CHOICES, null=True, blank=True)
    pendant = models.CharField(max_length=350, choices=DELAY_CHOICES, null=True, blank=True)
    a_partir_de = models.CharField(max_length=350, choices=FROM_CHOICES, null=True, blank=True)
    prescribed_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Dispensed', 'Dispensed'),
        ('Cancelled', 'Cancelled')
    ])
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='prescription_creator')

    executed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                    related_name='executed_prescriptions')
    executed_at = models.DateTimeField(null=True, blank=True)
    observations = models.TextField(null=True, blank=True, help_text="Notes ou observations lors de l'exécution.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def normalize_string(value):
        """
        Normalise une chaîne en minuscule, sans accents, et supprime les espaces inutiles.
        """
        if not value:
            return None
        # Supprime les accents
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        # Convertit en minuscule et supprime les espaces superflus
        return ' '.join(value.lower().split())

    def generate_executions(self):
        """
        Génère les prises de médicament en fonction de la posologie, de la durée du traitement, et du délai avant la première prise.
        """
        POSOLOGY_MAPPING = {
            'une fois par jour': 24,
            'deux fois par jour': 12,
            'trois fois par jour': 8,
            'quatre fois par jour': 6,
            'toutes les 4 heures': 4,
            'toutes les 6 heures': 6,
            'toutes les 8 heures': 8,
            'si besoin': None,
            'avant les repas': None,
            'après les repas': None,
            'au coucher': None,
            'une fois par semaine': None,
            'deux fois par semaine': None,
            'un jour sur deux': None,
        }

        # Normaliser la posologie
        normalized_posology = self.normalize_string(self.posology)
        interval = POSOLOGY_MAPPING.get(normalized_posology)

        if interval is None:
            # Si la posologie n'est pas basée sur un intervalle (ex. : "Si besoin"), ne rien générer
            return

        # Calcul de la durée du traitement
        try:
            duration_days = int(self.pendant)
        except (TypeError, ValueError):
            # Par défaut, limiter à 1 jour si `pendant` n'est pas défini ou invalide
            duration_days = 1

        # Calcul du délai avant la première prise
        try:
            delay_hours = int(self.a_partir_de)  # Convertir la valeur de `a_partir_de` en heures
        except (TypeError, ValueError):
            delay_hours = 0  # Par défaut, aucune attente avant la première prise

        start_time = self.prescribed_at + datetime.timedelta(hours=delay_hours)  # Ajoute le délai à la prescription
        end_time = self.prescribed_at + datetime.timedelta(days=duration_days)

        # Récupérer toutes les exécutions existantes pour cette prescription
        existing_executions = set(
            PrescriptionExecution.objects.filter(prescription=self).values_list('scheduled_time', flat=True)
        )

        # Génération des exécutions
        new_executions = []
        while start_time < end_time:
            if start_time not in existing_executions:
                new_executions.append(
                    PrescriptionExecution(
                        prescription=self,
                        scheduled_time=start_time,
                        status='Pending',
                    )
                )
            start_time += datetime.timedelta(hours=interval)

        # Utiliser une transaction pour insérer toutes les nouvelles exécutions en une seule requête
        if new_executions:
            with transaction.atomic():
                PrescriptionExecution.objects.bulk_create(new_executions)

    def __str__(self):
        return f"{self.patient.nom} - {self.medication.nom}"


class PrescriptionExecution(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="executions")
    scheduled_time = models.DateTimeField()  # Heure prévue de la prise
    executed_at = models.DateTimeField(null=True, blank=True)  # Heure réelle de la prise
    executed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="executed_meds")
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Taken', 'Taken'),
        ('Missed', 'Missed'),
    ], default='Pending')
    observations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.prescription.medication.nom} - {self.scheduled_time} - {self.status}"


class WaitingRoom(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='waiting_rooms')
    arrival_time = models.DateTimeField(default=timezone.now)
    reason = models.TextField()
    status = models.CharField(max_length=50, choices=[
        ('Waiting', 'Waiting'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ])
    medecin = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='waiting_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.arrival_time}"


class TraitementARV(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='traitements_arv')
    regime = models.CharField(max_length=255, help_text="Schéma thérapeutique ARV.")
    date_debut = models.DateField(help_text="Date de début du traitement ARV.")
    date_fin = models.DateField(blank=True, null=True, help_text="Date de fin du traitement si applicable.")
    adherence = models.CharField(max_length=20, choices=[
        ('Bonne', 'Bonne'),
        ('Moyenne', 'Moyenne'),
        ('Faible', 'Faible')
    ], default='Bonne', help_text="Niveau d'adhérence au traitement.")

    def __str__(self):
        return f"Traitement ARV {self.regime} pour {self.patient}"


class FicheSuiviClinique(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    medecin = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='fichemedecinsuivi')
    date_consultation = models.DateField(help_text="Date de la consultation.")
    heure_consultation = models.TimeField(help_text="Heure de la consultation.", blank=True, null=True)
    observations_cliniques = models.TextField(blank=True, null=True, help_text="Observations cliniques du médecin.")
    poids = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                help_text="Poids du patient en kg.")
    taille = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                 help_text="Taille du patient en cm.")
    pression_arterielle = models.CharField(max_length=20, blank=True, null=True, help_text="Exemple : 120/80 mmHg")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True,
                                      help_text="Température corporelle en °C.")
    recommandations = models.TextField(blank=True, null=True, help_text="Recommandations du médecin pour le patient.")
    prochaine_consultation = models.DateField(blank=True, null=True,
                                              help_text="Date de la prochaine consultation prévue.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation de {self.patient} avec {self.medecin} le {self.date_consultation}"


class Suivi(models.Model):
    activite = models.ForeignKey(ServiceSubActivity, on_delete=models.CASCADE, related_name="suiviactivitepat",
                                 null=True,
                                 blank=True, )
    services = models.ForeignKey(Service, on_delete=models.SET_NULL, blank=True, null=True,
                                 related_name='servicesuivipat')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="suivimedecin")
    fichesuivie = models.ForeignKey(FicheSuiviClinique, on_delete=models.CASCADE, related_name='suivisfiche')
    traitement = models.ForeignKey(TraitementARV, on_delete=models.CASCADE, related_name='suivispatient', null=True,
                                   blank=True)
    rdvconsult = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='suivierdvconsult', null=True,
                                   blank=True)
    rdvpharmacie = models.ForeignKey(RendezVous, on_delete=models.CASCADE, related_name='suivierdvpharma', null=True,
                                     blank=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.services}"


class Hospitalization(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hospitalized')
    activite = models.ForeignKey(ServiceSubActivity, on_delete=models.CASCADE, related_name="acti_hospitalied",
                                 null=True, blank=True, )
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hospitaliza_doctor')
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True, blank=True)
    discharge_reason = models.CharField(max_length=700, null=True, blank=True)
    room = models.CharField(max_length=500)
    bed = models.ForeignKey('LitHospitalisation', related_name='lit_hospy', on_delete=models.SET_NULL, null=True,
                            blank=True)
    reason_for_admission = models.TextField()
    status = models.CharField(max_length=50, choices=Patient_statut_choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.admission_date}"


class SigneFonctionnel(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    valeure = models.CharField(choices=[('oui', 'oui'), ('non', 'non')], max_length=255)
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.SET_NULL, related_name='signefonctionnels',
                                        null=True, blank=True)

    def __str__(self):
        return self.nom


class IndicateurBiologique(models.Model):
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.CASCADE,
                                        related_name='indicateurs_biologiques')
    date = models.DateField(default=datetime.date.today)

    globules_blancs = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hemoglobine = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    plaquettes = models.IntegerField(null=True, blank=True)
    crp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    glucose_sanguin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Indicateurs biologiques pour {self.hospitalisation.patient.nom} le {self.date}"


class IndicateurFonctionnel(models.Model):
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.CASCADE,
                                        related_name='indicateurs_fonctionnels')
    date = models.DateField(default=datetime.date.today)

    mobilite = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('indépendant', 'Indépendant'),
        ('assisté', 'Assisté'),
        ('immobile', 'Immobile')
    ])
    conscience = models.CharField(max_length=50, null=True, blank=True, choices=[
        ('alerte', 'Alerte'),
        ('somnolent', 'Somnolent'),
        ('inconscient', 'Inconscient')
    ])
    debit_urinaire = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Litres")

    def __str__(self):
        return f"Indicateurs fonctionnels pour {self.hospitalisation.patient.nom} le {self.date}"


class IndicateurSubjectif(models.Model):
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.CASCADE,
                                        related_name='indicateurs_subjectifs')
    date = models.DateField(default=datetime.date.today)

    bien_etre = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(0, 11)])

    def __str__(self):
        return f"Indicateurs subjectifs pour {self.hospitalisation.patient.nom} le {self.date}"


class HospitalizationIndicators(models.Model):
    # Indicateurs de Complications
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.CASCADE, related_name='indicateurs_autres',
                                        null=True, blank=True, )
    temperature = models.FloatField(null=True, blank=True, help_text="Température en degrés Celsius")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Fréquence cardiaque (bpm)")
    respiratory_rate = models.IntegerField(null=True, blank=True, help_text="Fréquence respiratoire (rpm)")
    blood_pressure = models.CharField(max_length=20, null=True, blank=True,
                                      help_text="Tension artérielle (ex : 120/80 mmHg)")
    pain_level = models.IntegerField(null=True, blank=True, help_text="Niveau de douleur sur une échelle de 1 à 10")
    mental_state = models.CharField(max_length=20,
                                    choices=[
                                        ('clair', 'Clair'),
                                        ('confusion', 'Confusion'),
                                        ('somnolent', 'Somnolent'),
                                    ],
                                    null=True,
                                    blank=True,
                                    help_text="État de conscience du patient"
                                    )

    # Indicateurs de Traitement
    treatment_response = models.TextField(null=True, blank=True, help_text="Réponse du patient au traitement")
    side_effects = models.TextField(null=True, blank=True, help_text="Effets secondaires observés")
    compliance = models.BooleanField(default=False, help_text="Observance du traitement")
    electrolytes_balance = models.CharField(max_length=50, null=True, blank=True, help_text="Équilibre électrolytique")
    renal_function = models.CharField(max_length=50, null=True, blank=True, help_text="État de la fonction rénale")
    hepatic_function = models.CharField(max_length=50, null=True, blank=True, help_text="État de la fonction hépatique")

    # Indicateurs de Sortie (Critères de décharge)
    stable_vitals = models.BooleanField(default=False, help_text="Les signes vitaux sont-ils stables?")
    pain_controlled = models.BooleanField(default=False, help_text="La douleur est-elle contrôlée?")
    functional_ability = models.BooleanField(default=False, help_text="Capacité fonctionnelle atteinte?")
    mental_stability = models.BooleanField(default=False, help_text="État mental stable?")
    follow_up_plan = models.TextField(null=True, blank=True, help_text="Plan de suivi post-hospitalisation")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Indicateurs d'hospitalisation pour patient {self.id} - {self.created_at.strftime('%Y-%m-%d')}"


class ComplicationsIndicators(models.Model):
    # Constantes des valeurs de référence
    SODIUM_NORMAL_RANGE = (135, 145)  # mmol/L
    POTASSIUM_NORMAL_RANGE = (3.5, 5.0)  # mmol/L
    CHLORURE_NORMAL_RANGE = (96, 106)  # mmol/L
    CALCIUM_NORMAL_RANGE = (2.1, 2.6)  # mmol/L
    MAGNESIUM_NORMAL_RANGE = (0.7, 1.1)  # mmol/L
    PHOSPHATE_NORMAL_RANGE = (0.8, 1.5)  # mmol/L
    CREATININE_NORMAL_RANGE_MALE = (60, 115)  # µmol/L
    CREATININE_NORMAL_RANGE_FEMALE = (45, 105)  # µmol/L
    BUN_NORMAL_RANGE = (7, 20)  # mg/dL
    ALT_NORMAL_RANGE = (7, 56)  # U/L
    AST_NORMAL_RANGE = (10, 40)  # U/L
    BILIRUBINE_TOTAL_NORMAL_RANGE = (0.1, 1.2)  # mg/dL
    ALBUMINE_NORMAL_RANGE = (3.5, 5.0)  # g/dL
    ALP_NORMAL_RANGE = (44, 147)  # U/L

    # Champs du modèle
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE,
                                        related_name='indicateurs_compliques', null=True, blank=True)
    sodium = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    potassium = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    chlorure = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    calcium = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    magnesium = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    phosphate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    creatinine = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bun = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    alt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ast = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bilirubine_totale = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    albumine = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    alp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Méthodes de vérification
    def is_sodium_normal(self):
        return self.SODIUM_NORMAL_RANGE[0] <= self.sodium <= self.SODIUM_NORMAL_RANGE[
            1] if self.sodium is not None else None

    def is_potassium_normal(self):
        return self.POTASSIUM_NORMAL_RANGE[0] <= self.potassium <= self.POTASSIUM_NORMAL_RANGE[
            1] if self.potassium is not None else None

    def is_chlorure_normal(self):
        return self.CHLORURE_NORMAL_RANGE[0] <= self.chlorure <= self.CHLORURE_NORMAL_RANGE[
            1] if self.chlorure is not None else None

    def is_calcium_normal(self):
        return self.CALCIUM_NORMAL_RANGE[0] <= self.calcium <= self.CALCIUM_NORMAL_RANGE[
            1] if self.calcium is not None else None

    def is_magnesium_normal(self):
        return self.MAGNESIUM_NORMAL_RANGE[0] <= self.magnesium <= self.MAGNESIUM_NORMAL_RANGE[
            1] if self.magnesium is not None else None

    def is_phosphate_normal(self):
        return self.PHOSPHATE_NORMAL_RANGE[0] <= self.phosphate <= self.PHOSPHATE_NORMAL_RANGE[
            1] if self.phosphate is not None else None

    def is_creatinine_normal(self, gender):
        # Utiliser la plage normale basée sur le sexe
        if gender == 'male':
            return self.CREATININE_NORMAL_RANGE_MALE[0] <= self.creatinine <= self.CREATININE_NORMAL_RANGE_MALE[
                1] if self.creatinine is not None else None
        else:
            return self.CREATININE_NORMAL_RANGE_FEMALE[0] <= self.creatinine <= self.CREATININE_NORMAL_RANGE_FEMALE[
                1] if self.creatinine is not None else None

    def is_bun_normal(self):
        return self.BUN_NORMAL_RANGE[0] <= self.bun <= self.BUN_NORMAL_RANGE[1] if self.bun is not None else None

    def is_alt_normal(self):
        return self.ALT_NORMAL_RANGE[0] <= self.alt <= self.ALT_NORMAL_RANGE[1] if self.alt is not None else None

    def is_ast_normal(self):
        return self.AST_NORMAL_RANGE[0] <= self.ast <= self.AST_NORMAL_RANGE[1] if self.ast is not None else None

    def is_bilirubine_totale_normal(self):
        return self.BILIRUBINE_TOTAL_NORMAL_RANGE[0] <= self.bilirubine_totale <= self.BILIRUBINE_TOTAL_NORMAL_RANGE[
            1] if self.bilirubine_totale is not None else None

    def is_albumine_normal(self):
        return self.ALBUMINE_NORMAL_RANGE[0] <= self.albumine <= self.ALBUMINE_NORMAL_RANGE[
            1] if self.albumine is not None else None

    def is_alp_normal(self):
        return self.ALP_NORMAL_RANGE[0] <= self.alp <= self.ALP_NORMAL_RANGE[1] if self.alp is not None else None

    def __str__(self):
        return f"Indicateurs de complications pour hospitalisation {self.hospitalisation.id}"


class UniteHospitalisation(models.Model):
    nom = models.CharField(max_length=100)
    capacite = models.PositiveIntegerField(default=1)
    type = models.CharField(max_length=100)

    def __str__(self): return self.nom


class ChambreHospitalisation(models.Model):
    unite = models.ForeignKey(UniteHospitalisation, on_delete=models.CASCADE, related_name='chambres')
    nom = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.nom} - {self.unite}'


class BoxHospitalisation(models.Model):
    chambre = models.ForeignKey(ChambreHospitalisation, on_delete=models.CASCADE, related_name='boxes')
    capacite = models.PositiveIntegerField(default=1)
    nom = models.CharField(max_length=100)
    occuper = models.BooleanField(default=False)
    occupant = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.nom} - {self.chambre}'


class LitHospitalisation(models.Model):
    box = models.ForeignKey(BoxHospitalisation, on_delete=models.CASCADE, related_name='lits')
    nom = models.CharField(max_length=100, default='lit')
    occuper = models.BooleanField(default=False)
    occupant = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    reserved = models.BooleanField(default=False)
    reserved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    reserved_until = models.DateTimeField(null=True, blank=True)
    is_out_of_service = models.BooleanField(default=False)
    is_cleaning = models.BooleanField(default=False)
    status_changed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.nom} - {self.box}--{self.box.chambre.unite}'

    def reserve(self, employee):
        """
        Mark the bed as reserved by the given employee for 48 hours.
        """
        self.reserved_by = employee
        self.reserved = True
        self.reserved_until = timezone.now() + datetime.timedelta(hours=48)
        self.occuper = False
        self.is_out_of_service = False
        self.is_cleaning = False
        self.save()

    def release_if_unoccupied(self):
        """
        Release the bed if it's reserved but unoccupied and the reservation has expired.
        """
        if self.reserved_until and timezone.now() > self.reserved_until and not self.occupant:
            self.reserved_by = None
            self.reserved_until = None
            self.occuper = False
            self.save()

    def release_direct_unoccupied(self):
        """
        Release the bed if it's reserved but unoccupied and the reservation has expired.
        """
        if self.reserved_until and not self.occupant:
            self.reserved_by = None
            self.reserved_until = None
            self.occuper = False
            self.save()

    def assign_patient(self, patient, employee):
        """
        Assign a patient to the bed only if the employee is the one who reserved it.
        """
        if self.reserved_by == employee and timezone.now() <= self.reserved_until:
            self.occupant = patient
            self.occuper = True
            self.save()
        else:
            raise PermissionError("Only the reserving employee can assign a patient within the reservation period.")

    def mark_as_out_of_service(self):
        """
        Mark the bed as out of service and set the timestamp.
        """
        self.is_out_of_service = True
        self.occuper = False
        self.occupant = None
        self.reserved_by = None
        self.reserved_until = None
        self.status_changed_at = timezone.now()
        self.save()

    def mark_as_cleaning(self):
        """
        Mark the bed as in cleaning mode and set the timestamp.
        """
        self.is_cleaning = True
        self.occuper = False
        self.occupant = None
        self.reserved_by = None
        self.reserved_until = None
        self.status_changed_at = timezone.now()
        self.save()

    def is_timer_expired(self):
        """
        Check if 20 minutes have passed since the bed was marked as out of service or cleaning.
        """
        if self.status_changed_at:
            return timezone.now() >= self.status_changed_at + datetime.timedelta(minutes=20)
        return False

    def delete_bed(self):
        """
        Safely delete the bed from the database.
        """
        self.delete()

#---- Partie Pharmacie
