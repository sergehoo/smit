import datetime
import io
import random
import unicodedata
import uuid

from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.db.models import Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now
from django_countries.fields import CountryField
from schedule.models import Calendar, Event
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from tinymce.models import HTMLField

from core.models import Patient, Service, Employee, ServiceSubActivity, Patient_statut_choices, Maladie
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
    # Lettres de base
    WordStack = ['S', 'M', 'I', 'T', 'C', '', 'I']
    random_str = ''.join(random.choices(WordStack, k=2))  # Combine 2 lettres aléatoires
    current_date = datetime.datetime.now().strftime("%Y%m%d")  # Date au format AAAAMMJJ
    random_number = random.randint(1000, 9999)  # Nombre aléatoire à 4 chiffres
    unique_id = uuid.uuid4().hex[:6]  # Identifiant unique basé sur UUID (6 caractères)

    # Combinaison finale
    tracking = f"{random_str}-{random_number}-{current_date}-{unique_id}"
    return tracking


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name="appointmentsservice")
    doctor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="doctor_appointments")
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="calendar_appointments")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True, related_name="event_appointments")
    date = models.DateField()
    time = models.TimeField()
    reason = models.CharField(max_length=255)

    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Scheduled")

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='appointments_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"

    def __str__(self):
        return f"{self.patient.nom} - {self.date} {self.time} ({self.status})"


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


class TypeProtocole(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du type de protocole")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='type_protocoles')

    def __str__(self):
        return self.nom


class Protocole(models.Model):
    nom = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    type_protocole = models.ForeignKey(TypeProtocole, on_delete=models.SET_NULL, null=True, blank=True)
    duree = models.PositiveIntegerField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    molecules = models.ManyToManyField(Molecule)
    medicament = models.ManyToManyField(Medicament, verbose_name="Médicaments et posologies", blank=True)
    maladies = models.ForeignKey(Maladie, related_name="protocolesmaladies", on_delete=models.SET_NULL,
                                 verbose_name="Maladies traitées", null=True, blank=True)
    examens = models.ManyToManyField('Examen', related_name="protocolesexam", blank=True, verbose_name="Examens requis")

    def save(self, *args, **kwargs):
        if self.date_debut and self.duree:
            self.date_fin = self.date_debut + datetime.timedelta(days=self.duree)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} - {self.type_protocole.nom}"


class SuiviProtocole(models.Model):
    protocole = models.ForeignKey(Protocole, on_delete=models.CASCADE, related_name="etapes")
    suivi = models.ForeignKey('Suivi', on_delete=models.CASCADE, related_name="protocolessuivi", null=True, blank=True)
    nom = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='suivicreator')

    def __str__(self):
        return f"{self.protocole.nom} - {self.nom}"


class Evaluation(models.Model):
    etape = models.ForeignKey(SuiviProtocole, on_delete=models.CASCADE, related_name="evaluations", null=True,
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
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="sous_types")

    def get_all_sous_types(self):
        """Récupérer tous les sous-types d'un type d'antécédent."""
        return self.sous_types.all()

    def __str__(self):
        return self.nom


class AntecedentsMedicaux(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="hospiantecedents",
                                        null=True, blank=True)
    nom = models.CharField(max_length=255, null=True, blank=True)
    type = models.ForeignKey(TypeAntecedent, on_delete=models.SET_NULL, null=True, blank=True)
    descriptif = models.CharField(max_length=255, null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Antecedents Medicaux for {self.patient.nom} on {self.created_at}"


class ModeDeVieCategorie(models.Model):
    """Catégories de mode de vie (ex: Consommation, Environnement, Sexualité, Loisirs)"""
    nom = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nom


class ModeDeVie(models.Model):
    """Informations sur le mode de vie du patient"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="modes_de_vie_patients")
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="hospimodedevie",
                                        null=True, blank=True)
    categorie = models.ForeignKey(ModeDeVieCategorie, on_delete=models.CASCADE, related_name="modes_de_vie")
    description = models.TextField(null=True, blank=True, help_text="Détails sur le mode de vie")
    frequence = models.CharField(
        max_length=100, choices=[
            ('quotidien', 'Quotidien'),
            ('hebdomadaire', 'Hebdomadaire'),
            ('mensuel', 'Mensuel'),
            ('occasionnel', 'Occasionnel'),
            ('rare', 'Rare'),
        ], null=True, blank=True
    )
    niveau_impact = models.CharField(
        max_length=50, choices=[
            ('aucun', 'Aucun'),
            ('faible', 'Faible'),
            ('modéré', 'Modéré'),
            ('élevé', 'Élevé'),
        ], null=True, blank=True, help_text="Impact sur la santé"
    )
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='mode_vie_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.categorie.nom}"


class AppareilType(models.Model):
    """Appareil du corps humain (ex: Respiratoire, Digestif, Cardiaque...)"""
    nom = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name="sous_types_appareil")

    def __str__(self):
        return self.nom


class Appareil(models.Model):
    """Appareil du corps humain (ex: Respiratoire, Digestif, Cardiaque...)"""
    hospitalisation = models.ForeignKey("Hospitalization", on_delete=models.CASCADE, related_name="examens_appareils",
                                        null=True, blank=True)  # ✅ Ajout du lien avec l'hospitalisation
    type_appareil = models.ForeignKey(AppareilType, on_delete=models.SET_NULL, null=True, blank=True)
    nom = models.CharField(max_length=255)
    etat = models.CharField(
        max_length=50,
        choices=[
            ('normal', 'Normal'),
            ('altéré', 'Altéré'),
            ('anormal', 'Anormal'),
            ('non-applicable', 'non-applicable')
        ], default='normal'
    )
    observation = models.TextField(help_text="Détails de l'examen clinique de l'organe")

    # class Meta:
    # unique_together = ('hospitalisation', 'nom')  # ✅ Évite la duplication

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                   related_name='appareil_control_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


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
    patients_requested = models.ForeignKey(Patient, blank=True, null=True, on_delete=models.CASCADE,
                                           verbose_name="patients")
    consultation = models.ForeignKey('Consultation', blank=True, null=True, on_delete=models.CASCADE,
                                     related_name='examen_for_consultation')
    number = models.CharField(blank=True, null=True, max_length=300)
    delivered_by = models.CharField(blank=True, null=True, max_length=300)
    delivered_contact = models.CharField(blank=True, null=True, max_length=300)
    delivered_services = models.CharField(blank=True, null=True, max_length=300)
    date = models.DateField(blank=True, null=True)
    analyses = models.ForeignKey('Analyse', on_delete=models.CASCADE, blank=True, related_name='examanalyse', null=True,
                                 verbose_name="Type d'analyse")
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
    diagnosis = models.CharField(max_length=300, blank=True, null=True, )
    commentaires = models.CharField(max_length=300, blank=True, null=True, )

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
        return f"Consultation #{self.numeros} - {self.patient.nom} ({self.consultation_date.strftime('%d/%m/%Y')})"


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
    po = models.FloatField(null=True, blank=True, verbose_name="Périmètre Ombilicale")

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='constantes_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def pb_status(self):
        if self.pb is None:
            return "Non mesuré"

        if self.patient.genre == "Homme":
            if self.pb < 24:
                return "Malnutrition sévère"
            elif 24 <= self.pb < 26:
                return "Malnutrition modérée"
            elif 26 <= self.pb <= 35:
                return "Normal"
            elif self.pb > 35:
                return "Obésité"
        elif self.patient.genre == "Femme":
            if self.pb < 23:
                return "Malnutrition sévère"
            elif 23 <= self.pb < 25:
                return "Malnutrition modérée"
            elif 25 <= self.pb <= 32:
                return "Normal"
            elif self.pb > 32:
                return "Obésité"
        else:
            return "Sexe non spécifié"

    @property
    def po_status(self):
        if self.po is None:
            return "Non mesuré"

        if self.patient.genre == "Homme":
            if self.po < 78:
                return "Insuffisance pondérale"
            elif 78 <= self.po <= 94:
                return "Normal"
            elif 95 <= self.po <= 102:
                return "Surpoids"
            elif self.po > 102:
                return "Obésité abdominale"
        elif self.patient.genre == "Femme":
            if self.po < 70:
                return "Insuffisance pondérale"
            elif 70 <= self.po <= 80:
                return "Normal"
            elif 81 <= self.po <= 88:
                return "Surpoids"
            elif self.po > 88:
                return "Obésité abdominale"
        else:
            return "Sexe non spécifié"

    @property
    def imc_status(self):
        if self.imc is None:
            return "IMC non calculé"

        # Définir les seuils en fonction du sexe
        if self.patient.genre == "Homme":
            if self.imc < 20:
                return "Maigreur"
            elif 20 <= self.imc <= 25:
                return "Normal"
            elif 25 < self.imc <= 30:
                return "Surpoids"
            elif 30 < self.imc <= 35:
                return "Obésité modérée"
            elif 35 < self.imc <= 40:
                return "Obésité sévère"
            else:
                return "Obésité morbide"
        elif self.patient.genre == "Femme":
            if self.imc < 18.5:
                return "Maigreur"
            elif 18.5 <= self.imc <= 24.9:
                return "Normal"
            elif 24.9 < self.imc <= 29.9:
                return "Surpoids"
            elif 29.9 < self.imc <= 34.9:
                return "Obésité modérée"
            elif 34.9 < self.imc <= 39.9:
                return "Obésité sévère"
            else:
                return "Obésité morbide"
        else:
            return "Sexe non spécifié"

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

            # Vérification pour le périmètre brachial
        if self.pb and not (20 <= self.pb <= 40):  # Ajustez les valeurs normales selon votre contexte
            alertes.append(f"Périmètre brachial anormal: {self.pb} cm")

            # Vérification pour le périmètre ombilical
        if self.po and not (70 <= self.po <= 120):  # Ajustez les valeurs normales selon votre contexte
            alertes.append(f"Périmètre ombilical anormal: {self.po} cm")

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
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="hospiprescriptions",
                                        null=True, blank=True)
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
    cancellation_reason = models.TextField(null=True, blank=True)  # Ajout du champ pour le motif
    cancellation_date = models.DateTimeField(null=True, blank=True)  # Ajout du champ pour la date du motif
    cancellation_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                        related_name='prescription_cancelled_by')  # Ajout du champ pour la date du motif
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
        Génère ou ajuste les prises de médicament en fonction de la posologie,
        de la durée du traitement et du délai avant la première prise.
        """

        # 🔄 Mappage des posologies avec leurs intervalles en heures
        POSOLOGY_MAPPING = {
            'Une fois par jour': 24,
            'Deux fois par jour': 12,
            'Trois fois par jour': 8,
            'Quatre fois par jour': 6,
            'Toutes les 4 heures': 4,
            'Toutes les 6 heures': 6,
            'Toutes les 8 heures': 8,
            'Si besoin': None,
            'Avant les repas': None,
            'Après les repas': None,
            'Au coucher': None,
            'Une fois par semaine': 168,  # 7 jours
            'Deux fois par semaine': 84,  # 3,5 jours
            'Un jour sur deux': 48,  # 2 jours
        }

        # 🔍 Vérification de la posologie
        normalized_posology = self.posology.strip()
        interval = POSOLOGY_MAPPING.get(normalized_posology)

        if interval is None:
            # Si la posologie ne suit pas un intervalle fixe, on ne génère pas d'exécutions
            return

        # 🔍 Vérification et conversion de `pendant` en jours
        try:
            duration_days = int(self.pendant)
        except (TypeError, ValueError):
            duration_days = 1  # Si la valeur est invalide, par défaut 1 jour

        # 🔍 Vérification et conversion de `a_partir_de` en heures
        try:
            delay_hours = int(self.a_partir_de)
        except (TypeError, ValueError):
            delay_hours = 0  # Par défaut, aucune attente

        # ✅ Si `a_partir_de = 0` (Maintenant), accorder un délai de 10 minutes
        if delay_hours == 0:
            start_time = self.prescribed_at + datetime.timedelta(minutes=10)
        else:
            start_time = self.prescribed_at + datetime.timedelta(hours=delay_hours)

        # 🔄 Définition de la fin du traitement
        end_time = self.prescribed_at + datetime.timedelta(days=duration_days)

        # 🔍 Récupération des exécutions existantes
        existing_executions = PrescriptionExecution.objects.filter(prescription=self).order_by('scheduled_time')

        # 🔄 Ajustement si une exécution a déjà été effectuée
        last_execution_done = existing_executions.filter(status='Done').order_by('-scheduled_time').first()

        if last_execution_done:
            start_time = last_execution_done.scheduled_time + datetime.timedelta(hours=interval)

        # 🔄 Génération des nouvelles exécutions
        new_executions = []
        while start_time < end_time:
            # Vérifie si l'exécution pour cet horaire existe déjà
            if not existing_executions.filter(scheduled_time=start_time).exists():
                new_executions.append(
                    PrescriptionExecution(
                        prescription=self,
                        scheduled_time=start_time,
                        status='Pending',
                    )
                )
            start_time += datetime.timedelta(hours=interval)

        # 🔄 Insérer les nouvelles exécutions en une seule transaction
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
        ('Cancelled', 'Cancelled'),
    ], default='Pending')
    observations = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.prescription.medication.nom} - {self.scheduled_time} - {self.status}"

    @classmethod
    def update_missed_executions(cls):
        """
        Met à jour toutes les exécutions en attente ("Pending") dont l'heure prévue est dépassée.
        """
        with transaction.atomic():
            nb_updated = cls.objects.filter(
                scheduled_time__lt=now(),
                status="Pending"
            ).update(status="Missed")

        print(f"📌 {nb_updated} exécutions de prescription mises à jour en 'Missed'.")


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


class TraitementARV(models.Model):
    suivi = models.ForeignKey('Suivi', on_delete=models.CASCADE, blank=True, null=True,
                              verbose_name=_("Détails du suivi"), related_name='suivitreatarv')
    # Informations de base sur le traitement
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="patientarv", blank=True, null=True, verbose_name=_("Patient")
    )
    nom = models.CharField(max_length=100, verbose_name=_("Nom du traitement ARV"), null=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    dosage = models.CharField(max_length=50, verbose_name=_("Dosage recommandé"), null=True, blank=True)
    forme_pharmaceutique = models.CharField(
        max_length=50,
        choices=[
            ('comprimé', _("Comprimé")),
            ('solution_orale', _("Solution orale")),
            ('injectable', _("Injectable")),
        ],
        verbose_name=_("Forme pharmaceutique")
        , null=True, blank=True)
    type_traitement = models.CharField(
        max_length=50,
        choices=[
            ('première_ligne', _("Traitement de première ligne")),
            ('deuxième_ligne', _("Traitement de deuxième ligne")),
            ('troisième_ligne', _("Traitement de troisième ligne")),
        ],
        default='première_ligne',
        verbose_name=_("Type de traitement"), null=True, blank=True
    )
    duree_traitement = models.PositiveIntegerField(
        verbose_name=_("Durée du traitement (en mois)"), null=True, blank=True
    )
    posologie_details = models.TextField(
        blank=True, null=True, verbose_name=_("Détails sur la posologie")
    )

    # Statistiques et suivi
    effet_secondaire_courant = models.TextField(
        blank=True, null=True, verbose_name=_("Effets secondaires courants")
    )
    interaction_medicamenteuse = models.TextField(
        blank=True, null=True, verbose_name=_("Interactions médicamenteuses connues")
    )
    efficacite = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        verbose_name=_("Efficacité estimée (%)")
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name=_("Dernière mise à jour"))

    class Meta:
        verbose_name = _("Traitement ARV")
        verbose_name_plural = _("Traitements ARV")
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} - {self.type_traitement}"


class Suivi(models.Model):
    # Relations
    mode = models.CharField(max_length=50, choices=[
        ('permanent', 'Permanent'),
        ('occasionnel', 'Occasionnel'),
        ('periodique', 'Periodique')
    ], blank=True, null=True, )
    activite = models.ForeignKey(
        ServiceSubActivity, on_delete=models.CASCADE, related_name="suiviactivitepat",
        null=True, blank=True, verbose_name=_("Activité")
    )
    services = models.ForeignKey(
        Service, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='servicesuivipat', verbose_name=_("Service")
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="suivimedecin", verbose_name=_("Patient")
    )

    rdvconsult = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name='suivierdvconsult', null=True, blank=True,
        verbose_name=_("Rendez-vous de consultation")
    )
    rdvpharmacie = models.ForeignKey(
        RendezVous, on_delete=models.CASCADE, related_name='suivierdvpharma', null=True, blank=True,
        verbose_name=_("Rendez-vous en pharmacie")
    )

    # Nouveaux champs
    date_suivi = models.DateField(verbose_name=_("Date du suivi"), null=True, blank=True)
    statut_patient = models.CharField(
        max_length=50,
        choices=[
            ('actif', _("Actif")),
            ('perdu_de_vue', _("Perdu de vue")),
            ('transferé', _("Transféré")),
            ('décédé', _("Décédé")),
        ],
        default='actif',
        verbose_name=_("Statut du patient")
    )
    adherence_traitement = models.CharField(
        max_length=20,
        choices=[
            ('bonne', _("Bonne")),
            ('moyenne', _("Moyenne")),
            ('faible', _("Faible")),
        ],
        default='bonne',
        verbose_name=_("Adhérence au traitement")
    )
    poids = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("Poids du patient (kg)")
    )
    cd4 = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Taux de CD4"))
    charge_virale = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Charge virale"))
    observations = models.TextField(
        null=True, blank=True, verbose_name=_("Observations générales")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Métadonnées
    class Meta:
        verbose_name = _("Suivi de patient VIH")
        verbose_name_plural = _("Suivis de patients VIH")
        ordering = ['-date_suivi']

    def __str__(self):
        return f"{self.patient.nom} - {self.services} - {self.date_suivi}"


class InfectionOpportuniste(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="infections_opportunistes",
        verbose_name=_("Patient")
    )
    type_infection = models.CharField(
        max_length=255,
        verbose_name=_("Type d'infection")
    )
    date_diagnostic = models.DateField(
        verbose_name=_("Date de diagnostic")
    )
    gravite = models.CharField(
        max_length=20,
        choices=[
            ('faible', _("Faible")),
            ('modérée', _("Modérée")),
            ('sévère', _("Sévère")),
        ],
        default='faible',
        verbose_name=_("Gravité")
    )
    traitement = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Traitement")
    )
    statut_traitement = models.CharField(
        max_length=20,
        choices=[
            ('en cours', _("En cours")),
            ('terminé', _("Terminé")),
            ('abandonné', _("Abandonné")),
        ],
        default='en cours',
        verbose_name=_("Statut du traitement")
    )
    suivi = models.ForeignKey(Suivi, on_delete=models.CASCADE, blank=True, null=True,
                              verbose_name=_("Détails du suivi"), related_name='suiviinfections')
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    def __str__(self):
        return f"{self.type_infection} chez {self.patient.nom}"

    class Meta:
        verbose_name = _("Infection Opportuniste")
        verbose_name_plural = _("Infections Opportunistes")
        ordering = ['-date_diagnostic']


class Comorbidite(models.Model):
    suivi = models.ForeignKey(Suivi, on_delete=models.CASCADE, blank=True, null=True,
                              verbose_name=_("Détails du suivi"), related_name='suivicomorbide')

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="comorbidites",
        verbose_name=_("Patient")
    )
    type_comorbidite = models.CharField(
        max_length=255,
        verbose_name=_("Type de comorbidité")
    )
    date_diagnostic = models.DateField(
        verbose_name=_("Date de diagnostic")
    )
    traitement = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Traitement")
    )
    statut_traitement = models.CharField(
        max_length=20,
        choices=[
            ('en cours', _("En cours")),
            ('terminé', _("Terminé")),
            ('abandonné', _("Abandonné")),
        ],
        default='en cours',
        verbose_name=_("Statut du traitement")
    )
    impact_sur_vih = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Impact sur le VIH"),
        help_text=_("Expliquez comment cette comorbidité influence la gestion du VIH.")
    )
    recommandations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Recommandations"),
        help_text=_("Recommandations spécifiques liées à cette comorbidité.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    def __str__(self):
        return f"{self.type_comorbidite} chez {self.patient.nom}"

    class Meta:
        verbose_name = _("Comorbidité")
        verbose_name_plural = _("Comorbidités")
        ordering = ['-date_diagnostic']


class Vaccination(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="vaccinations",
        verbose_name=_("Patient")
    )
    type_vaccin = models.CharField(
        max_length=255,
        verbose_name=_("Type de vaccin"),
        help_text=_("Exemple : Hépatite B, Pneumocoque, Grippe, etc.")
    )
    date_administration = models.DateField(
        verbose_name=_("Date d'administration")
    )
    centre_vaccination = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Centre de vaccination"),
        help_text=_("Lieu où la vaccination a été administrée.")
    )
    lot_vaccin = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Numéro de lot du vaccin"),
        help_text=_("Numéro de lot pour traçabilité.")
    )
    professionnel_sante = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Professionnel de santé"),
        help_text=_("Nom ou identifiant du professionnel ayant administré le vaccin.")
    )
    rappel_necessaire = models.BooleanField(
        default=False,
        verbose_name=_("Rappel nécessaire"),
        help_text=_("Indique si un rappel est nécessaire pour ce vaccin.")
    )
    date_rappel = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de rappel"),
        help_text=_("Date prévue pour le rappel, si applicable.")
    )
    effets_secondaires = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Effets secondaires signalés"),
        help_text=_("Décrire les effets secondaires éventuels observés après l'administration du vaccin.")
    )
    remarques = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Remarques"),
        help_text=_("Informations supplémentaires concernant la vaccination.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    def __str__(self):
        return f"Vaccination de {self.patient.nom} ({self.type_vaccin})"

    class Meta:
        verbose_name = _("Vaccination")
        verbose_name_plural = _("Vaccinations")
        ordering = ['-date_administration']


class ParaclinicalExam(models.Model):
    EXAM_TYPES = [
        ('Hémogramme', 'Hémogramme'),
        ('Ionogramme', 'Ionogramme'),
        ('Bilan hépatique', 'Bilan hépatique'),
        ('Bilan rénal', 'Bilan rénal'),
        ('Urines', 'Examen d’urines'),
        ('CRP', 'CRP'),
        ('PCT', 'PCT'),
        ('TP', 'TP'),
        ('TCA', 'TCA'),
        ('Glycémie', 'Glycémie'),
        ('HbA1C', 'HbA1C'),
        ('Tubage gastrique/Crachats', 'Tubage gastrique/Crachats'),
        ('LCR', 'LCR'),
        ('Gazometrie', 'Gazometrie'),
        ('Marquer Cardiaques', 'Marquer Cardiaques'),
        ('Selles', 'Selles'),
        ('CrAg', 'CrAg'),
        ('TB LAM', 'TB LAM'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="paraclinical_exams")
    # doctor = models.ForeignKey("Employee", on_delete=models.SET_NULL, null=True, related_name="prescribed_exams")
    hospitalisation = models.ForeignKey("Hospitalization", on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name="hospitalization_exams")

    exam_type = models.CharField(max_length=50, choices=EXAM_TYPES, verbose_name="Type d'Examen")
    exam_name = models.CharField(max_length=50, verbose_name="nom de l'Examen", null=True, blank=True)
    prescribed_at = models.DateTimeField(default=timezone.now)
    performed_at = models.DateTimeField(null=True, blank=True)

    result_value = models.IntegerField(null=True, blank=True, help_text="Résultats de l'examen en chiffre.")
    result_text = models.TextField(null=True, blank=True, help_text="Résultats de l'examen en texte.")
    result_file = models.FileField(upload_to="paraclinical_results/", null=True, blank=True)

    status = models.CharField(max_length=50, choices=[
        ('Pending', 'En attente'),
        ('Completed', 'Réalisé'),
        ('Cancelled', 'Annulé')
    ], default='Pending')
    # Suivi de l'évolution (1ère, 2ème, 3ème fois)
    iteration = models.PositiveIntegerField(default=1, help_text="Nombre de fois où cet examen a été réalisé.")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        """
        Avant de sauvegarder, déterminer l'iteration de cet examen pour le patient.
        """
        if not self.id:  # Uniquement pour les nouveaux examens
            previous_exams = ParaclinicalExam.objects.filter(patient=self.patient, exam_type=self.exam_type).count()
            self.iteration = previous_exams + 1  # Incrémente le nombre d'exécutions de cet examen

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.exam_type} (#{self.iteration}) - {self.patient.nom} ({self.get_status_display()})"


class Hospitalization(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hospitalized')
    activite = models.ForeignKey(ServiceSubActivity, on_delete=models.CASCADE, related_name="acti_hospitalied",
                                 null=True, blank=True, )
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hospitaliza_doctor')
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(null=True, blank=True)
    discharge_reason = models.CharField(max_length=700, null=True, blank=True)
    room = models.CharField(max_length=500)
    bed = models.ForeignKey('LitHospitalisation', related_name='lit_hospy', on_delete=models.RESTRICT, null=True,
                            blank=True)
    reason_for_admission = models.TextField()
    status = models.CharField(max_length=50, choices=Patient_statut_choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.nom} - {self.admission_date}"

    def clean(self):
        """Validation de la cohérence des dates."""
        from django.core.exceptions import ValidationError
        if self.discharge_date and self.discharge_date <= self.admission_date:
            raise ValidationError("La date de sortie doit être postérieure à la date d'admission.")

    def dernier_diagnostic(self):
        """Retourne le dernier diagnostic pour cette hospitalisation."""
        dernier = self.diagnostics.order_by('-date_diagnostic').first()
        return dernier

    def save(self, *args, **kwargs):
        """Annule les prescriptions restantes lorsqu'un patient est sorti."""
        previous_hospitalization = None
        if self.pk:
            previous_hospitalization = Hospitalization.objects.filter(pk=self.pk).first()

        # Sauvegarde de l'objet hospitalisation
        super().save(*args, **kwargs)

        # Vérifier si le patient vient d'être sorti (discharge_date vient d'être rempli)
        if previous_hospitalization and previous_hospitalization.discharge_date is None and self.discharge_date:
            self.annuler_prescriptions_restantes()

    def annuler_prescriptions_restantes(self):
        """Annule les exécutions restantes des prescriptions lorsque le patient quitte l'hôpital."""
        # import PrescriptionExecution  # Importer ici pour éviter les imports circulaires

        with transaction.atomic():
            PrescriptionExecution.objects.filter(
                prescription__hospitalisation=self,
                status="Pending"
            ).update(status="Cancelled")

        print(f"📢 Toutes les exécutions en attente du patient {self.patient.nom} ont été annulées.")


class Diagnostic(models.Model):
    DIAGNOSTIC_TYPE_CHOICES = [
        ('secondaire', 'Secondaire'),
        ('fonctionnel', 'Fonctionnel'),
        ('complication', 'Complication'),
        ('probable', 'Probable'),
        # ('possible', 'Possible'),
        ('final', 'Final'),
    ]

    maladie = models.ForeignKey(Maladie, on_delete=models.CASCADE, related_name="maladiediagnostics", null=True,
                                blank=True)
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="diagnostics")
    type_diagnostic = models.CharField(max_length=20, choices=DIAGNOSTIC_TYPE_CHOICES)
    nom = models.CharField(max_length=255)  # Nom de la condition ou pathologie
    date_diagnostic = models.DateTimeField()
    remarques = models.TextField(blank=True, null=True)  # Notes ou observations supplémentaires
    medecin_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.maladie} ({self.get_type_diagnostic_display()})"


class AvisMedical(models.Model):
    hospitalisation = models.ForeignKey(
        'Hospitalization',
        on_delete=models.CASCADE,
        related_name='avis_medicaux'
    )  # Association avec une hospitalisation spécifique
    medecin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avis_medicaux'
    )  # Médecin responsable de l'avis
    titre = models.CharField(max_length=255)  # Titre ou résumé de l'avis
    contenu = models.TextField(blank=True, null=True)  # Détails ou recommandations
    date_avis = models.DateTimeField(auto_now_add=True)  # Date et heure de l'avis
    mise_a_jour = models.DateTimeField(auto_now=True)  # Date de dernière mise à jour

    def __str__(self):
        return f"Avis médical : {self.titre} - {self.hospitalisation.patient}"


class EffetIndesirable(models.Model):
    hospitalisation = models.ForeignKey(
        'Hospitalization',
        on_delete=models.CASCADE,
        related_name='effets_indesirables'
    )  # Association avec une hospitalisation spécifique
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='effets_indesirables'
                                )  # Association avec le patient
    medecin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='effets_indesirables')  # Médecin qui a signalé l'effet
    description = models.TextField()  # Description détaillée de l'effet indésirable

    gravite = models.CharField(
        max_length=50,
        choices=[
            ('Léger', 'Léger'),
            ('Modéré', 'Modéré'),
            ('Grave', 'Grave')
        ],
        default='Léger'
    )  # Niveau de gravité
    date_apparition = models.DateField()  # Date d'apparition de l'effet
    medicament_associe = models.ForeignKey(Medicament, on_delete=models.SET_NULL, blank=True,
                                           null=True)  # Nom du médicament (si applicable)
    observations = models.TextField(blank=True, null=True)  # Autres observations
    date_signalement = models.DateTimeField(auto_now_add=True)  # Date de signalement

    def clean(self):
        # Vérifier si la date_apparition n'est pas None avant la comparaison
        if self.date_apparition and self.date_apparition > timezone.now().date():
            raise ValidationError("La date d'apparition ne peut pas être dans le futur.")

    def __str__(self):
        return f"Effet Indésirable ({self.gravite}) - {self.patient}"


class HistoriqueMaladie(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='historiques_maladie'
                                , db_index=True)  # Associe l'historique au patient
    medecin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='historiques_maladie'
                                , db_index=True)  # Médecin ayant rédigé l'historique
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='historique_maladie_hospi',
                                        db_index=True)  # Médecin ayant ajouté l'observation

    date_enregistrement = models.DateTimeField(auto_now_add=True)  # Date d'enregistrement
    description = HTMLField()  # Détails de l'évolution de la maladie

    class Meta:
        verbose_name = "Historique de la Maladie"
        verbose_name_plural = "Historiques de Maladies"
        ordering = ['-date_enregistrement']  # Trie par défaut par date descendante

    def __str__(self):
        return f"Historique de {self.patient} ({self.date_enregistrement.strftime('%d/%m/%Y')})"


class ResumeSyndromique(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='patient_resume_syndromique'
                                , db_index=True)  # Associe l'historique au patient
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='resume_maladie_hospi',
                                        db_index=True)  # Médecin ayant ajouté l'observation
    description = HTMLField()  # Détails de l'évolution de la maladie

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='resumer_reccorder')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "resume syndromique de la Maladie"
        # verbose_name_plural = "Historiques de Maladies"
        ordering = ['-created_at']  # Trie par défaut par date descendante

    def __str__(self):
        return f"resume de {self.patient} ({self.created_at.strftime('%d/%m/%Y')})"


class ProblemePose(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='patient_maladie_probleme'
                                , db_index=True)  # Associe l'historique au patient
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='probleme_maladie_hospi',
                                        db_index=True)  # Médecin ayant ajouté l'observation
    description = HTMLField()  # Détails de l'évolution de la maladie

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True,
                                   related_name='probleme_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "resume syndromique de la Maladie"
        # verbose_name_plural = "Historiques de Maladies"
        ordering = ['-created_at']  # Trie par défaut par date descendante

    def __str__(self):
        return f"resume de {self.patient} ({self.created_at.strftime('%d/%m/%Y')})"


class TypeBilanParaclinique(models.Model):
    nom = models.CharField(max_length=250, unique=True, verbose_name="Nom du type de bilan")

    def __str__(self):
        return self.nom


class ExamenStandard(models.Model):
    type_examen = models.ForeignKey(TypeBilanParaclinique, on_delete=models.CASCADE, null=True, blank=True,
                                    verbose_name="Type d'examen")
    nom = models.CharField(max_length=250, unique=True, verbose_name="Nom de l'examen")

    def __str__(self):
        return self.nom


class BilanParaclinique(models.Model):
    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="bilans",
                                verbose_name="bilanparacliniquepatient", null=True, blank=True, )
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.CASCADE, related_name="bilans",
                                        verbose_name="hospitalisation_bilan_paraclinique", null=True, blank=True, )
    examen = models.ForeignKey(ExamenStandard, on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name="Examen demandé")

    description = models.TextField(null=True, blank=True, verbose_name="Description de l'examen")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    result = models.CharField(max_length=250, null=True, blank=True, verbose_name="Résultat")
    result_date = models.DateTimeField(verbose_name="Date du résultat", null=True, blank=True, )
    reference_range = models.CharField(max_length=250, null=True, blank=True, verbose_name="Valeur de référence")
    unit = models.CharField(max_length=50, null=True, blank=True, verbose_name="Unité de mesure")
    doctor = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="bilans_medecin",
                               verbose_name="Médecin prescripteur")
    comment = models.TextField(null=True, blank=True, verbose_name="Commentaire du médecin")
    status = models.CharField(max_length=20, choices=STATUT_CHOICES, default='pending',
                              verbose_name="Statut de l'examen")
    report_file = models.FileField(upload_to="bilans/", null=True, blank=True, verbose_name="Fichier du rapport")

    def __str__(self):
        return f"{self.patient.nom} - {self.examen.nom if self.examen else 'Examen non spécifié'} -- {self.examen.type_examen.nom} ({self.get_status_display()})"


class TypeImagerie(models.Model):
    nom = models.CharField(max_length=250, unique=True, verbose_name="Type d'imagerie")

    def __str__(self):
        return self.nom


class ImagerieMedicale(models.Model):
    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours d’analyse'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="imageriespatient",
                                verbose_name="Patient")
    hospitalisation = models.ForeignKey('Hospitalization', on_delete=models.CASCADE, related_name="imagerieshospi",
                                        verbose_name="Hospitalisation", null=True, blank=True)
    type_imagerie = models.ForeignKey(TypeImagerie, on_delete=models.CASCADE, verbose_name="Type d'imagerie")
    prescription = models.TextField(verbose_name="Motif de la demande", null=True, blank=True)

    # Stockage des images et fichiers DICOM
    image_file = models.FileField(upload_to="imagerie/images/", null=True, blank=True,
                                  verbose_name="Fichier d'imagerie")
    dicom_file = models.FileField(upload_to="imagerie/dicom/", null=True, blank=True, verbose_name="Fichier DICOM")

    # Résultat & rapport
    interpretation = models.TextField(verbose_name="Interprétation du radiologue", null=True, blank=True)
    rapport_file = models.FileField(upload_to="imagerie/rapports/", null=True, blank=True,
                                    verbose_name="Fichier du rapport")

    # Informations supplémentaires
    status = models.CharField(max_length=20, choices=STATUT_CHOICES, default='pending',
                              verbose_name="Statut de l'examen")
    date_examen = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'examen")
    medecin_prescripteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                             related_name="medecin_imagerie", verbose_name="Médecin prescripteur")
    radiologue = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="radiologue",
                                   verbose_name="Radiologue")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return f"{self.patient.nom} - {self.type_imagerie.nom} ({self.get_status_display()})"


class Observation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,
                                related_name='observations', null=True, blank=True, )  # Patient lié à l'observation
    medecin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='observations')  # Médecin ayant ajouté l'observation
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='hospiobservations')  # Médecin ayant ajouté l'observation
    date_enregistrement = models.DateTimeField(auto_now_add=True)  # Date de l'enregistrement
    details = models.TextField(null=True)  # Contenu de l'observation
    statut = models.CharField(max_length=50, choices=[('Initiale', 'Initiale'), ('Intermédiaire', 'Intermédiaire'),
                                                      ('Finale', 'Finale'), ], default='Initiale')

    def __str__(self):
        return f"Observation pour {self.patient} ({self.date_enregistrement.strftime('%d/%m/%Y')})"

    def short_details(self, length=50):
        """Retourne un résumé des détails."""
        return self.details[:length] + "..." if len(self.details) > length else self.details


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


class CommentaireInfirmier(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,
                                related_name='commentpatient', null=True, blank=True, )  # Patient lié à l'observation
    medecin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='medecincomment')  # Médecin ayant ajouté l'observation
    hospitalisation = models.ForeignKey(Hospitalization, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='hospicomment')  # Médecin ayant ajouté l'observation
    date_commentaire = models.DateTimeField(auto_now_add=True)  # Date de création du commentaire
    contenu = models.TextField()  # Contenu du commentaire

    def __str__(self):
        return f"Commentaire de {self.medecin} sur {self.patient} ({self.date_commentaire.strftime('%d/%m/%Y')})"

    class Meta:
        verbose_name = "Commentaire Infirmier"
        verbose_name_plural = "Commentaires Infirmiers"
        ordering = ['-date_commentaire']  # Trie par date décroissante


class CathegorieEchantillon(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.nom} - {self.parent}"


class TypeEchantillon(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.nom


class Echantillon(models.Model):
    code_echantillon = models.CharField(null=True, blank=True, max_length=10)
    examen_demande = models.ForeignKey(Examen, null=True, blank=True, on_delete=models.CASCADE,
                                       related_name='examen_demandee')
    type = models.ForeignKey('TypeEchantillon', null=True, blank=True, on_delete=models.CASCADE)
    cathegorie = models.ForeignKey('CathegorieEchantillon', null=True, blank=True, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='echantillon_for_patient')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE,
                                     related_name='echantillon_for_consultation')
    date_collect = models.DateTimeField(null=True, blank=True)
    site_collect = models.CharField(null=True, blank=True, max_length=100)
    agent_collect = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)
    status_echantillons = models.CharField(null=True, blank=True, max_length=10)
    storage_information = models.CharField(null=True, blank=True, max_length=100)
    storage_location = models.CharField(null=True, blank=True, max_length=100)
    storage_temperature = models.CharField(null=True, blank=True, max_length=100)
    volume = models.FloatField(null=True, blank=True, max_length=100, verbose_name='Volume de l\'échantillon (ml)')
    expiration_date = models.CharField(null=True, blank=True, max_length=100)
    linked = models.BooleanField(default=False, null=True, blank=True)
    used = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    history = HistoricalRecords()

    # @property
    # def accusereception(self):
    #     """
    #     Renvoie les instances d'AccuseReception associées à cet échantillon.
    #     """
    #     return self.accusereception_set.all()

    def __str__(self):
        return f"{self.code_echantillon} - {self.examen_demande}"
