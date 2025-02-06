import random
import uuid
from datetime import timedelta

from PIL import Image
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from schedule.models import Calendar, Event
from django.core.files.storage import default_storage

FORME_MEDICAMENT_CHOICES = [
    ('comprime', 'comprime'),
    ('sirop', 'sirop'),
    ('injection', 'injection'),
    ('gelule', 'gelule'),
    ('creme', 'creme'),
    ('pommade', 'pommade'),
    ('suppositoire', 'suppositoire'),
    ('gouttes', 'gouttes'),
    ('patch', 'patch'),
    ('inhalateur', 'inhalateur'),
    ('solution', 'solution'),
    ('suspension', 'suspension'),
    ('poudre', 'poudre'),
    ('spray', 'spray'),
    ('ovule', 'ovule'),
    ('collyre', 'collyre'),  # pour les yeux
    ('aérosol', 'aérosol'),
    ('elixir', 'elixir'),
    ('baume', 'baume'),
    ('granulé', 'granulé'),
    ('capsule', 'capsule'),
]

UNITE_DOSAGE_CHOICES = [
    ('mg', 'Milligramme (mg)'),
    ('g', 'Gramme (g)'),
    ('ml', 'Millilitre (ml)'),
    ('L', 'Litre (L)'),
    ('mcg', 'Microgramme (mcg)'),
    ('UI', 'Unité Internationale (UI)'),
    ('meq', 'Milliequivalent (mEq)'),
    ('µL', 'Microlitre (µL)'),
    ('µg', 'Microgramme (µg)'),
    ('cm³', 'Centimètre Cube (cm³)'),
    ('mL/kg', 'Millilitre par kilogramme (mL/kg)'),
    ('mg/m²', 'Milligramme par mètre carré (mg/m²)'),
    ('mg/kg', 'Milligramme par kilogramme (mg/kg)'),
    ('g/L', 'Gramme par litre (g/L)'),
]


class CathegorieMolecule(models.Model):
    nom = models.CharField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nom


class Molecule(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    cathegorie = models.ForeignKey(CathegorieMolecule, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nom


# Fonction pour générer un code barre unique de 12 chiffres
def generate_unique_code_barre():
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])


class Pharmacy(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255, choices=FORME_MEDICAMENT_CHOICES)
    description = models.TextField(null=True, blank=True)
    lieu = models.CharField(max_length=255)
    responsable = models.ForeignKey('core.Employee', on_delete=models.SET_NULL, null=True,
                                    blank=True)  # Use string reference

    def __str__(self):
        return f'{self.nom} {self.lieu}'


class Medicament(models.Model):
    codebarre = models.CharField(max_length=150, unique=True, default=generate_unique_code_barre,
                                 help_text="Code unique pour le médicament", validators=[
            RegexValidator(regex=r'^\d{12}$',
                           message="Le code-barre doit être composé de 12 chiffres.")])  # Pour l'identification par code-barre
    nom = models.CharField(max_length=255, null=True, blank=True, unique=True)
    dosage = models.IntegerField(null=True, blank=True)
    unitdosage = models.CharField(max_length=50, choices=UNITE_DOSAGE_CHOICES, null=True, blank=True,
                                  help_text="Ex: 500mg, 20mg/ml")
    dosage_form = models.CharField(max_length=50, choices=FORME_MEDICAMENT_CHOICES, null=True, blank=True)
    description = models.TextField(null=True, blank=True, )
    stock = models.PositiveIntegerField(null=True, blank=True, default=0)
    date_expiration = models.DateField(null=True, blank=True, )
    categorie = models.ForeignKey(CathegorieMolecule, on_delete=models.SET_NULL, null=True, blank=True)
    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.SET_NULL, null=True, blank=True)
    molecules = models.ManyToManyField(Molecule)
    miniature = models.ImageField(upload_to="pharmacy/miniature", null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Enregistrez d'abord l'image originale

        if self.miniature:
            miniature_path = self.miniature.path
            with Image.open(miniature_path) as img:
                # Convertir en RGB si nécessaire (utile pour les formats non RGB comme PNG)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Étape 1 : Redimensionner pour couvrir le cadre tout en conservant les proportions
                img_ratio = img.width / img.height
                target_ratio = 200 / 100

                if img_ratio > target_ratio:
                    # Image trop large, réduire la largeur
                    new_height = 100
                    new_width = int(new_height * img_ratio)
                else:
                    # Image trop haute, réduire la hauteur
                    new_width = 200
                    new_height = int(new_width / img_ratio)

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Étape 2 : Rogner pour obtenir exactement 150x100
                left = (new_width - 200) / 2
                top = (new_height - 100) / 2
                right = left + 200
                bottom = top + 100

                img = img.crop((left, top, right, bottom))

                # Étape 3 : Enregistrer avec une qualité élevée
                img.save(miniature_path, format="JPEG", quality=100)

    def __str__(self):
        return f'{self.nom} {self.dosage_form} {self.dosage} {self.unitdosage}'


class Medocsprescrits(models.Model):
    nom = models.CharField(max_length=355, null=True, blank=True, unique=True)
    dosage = models.IntegerField(null=True, blank=True)
    unitdosage = models.CharField(max_length=50, choices=UNITE_DOSAGE_CHOICES, null=True, blank=True,help_text="Ex: 500mg, 20mg/ml")
    dosage_form = models.CharField(max_length=50, choices=FORME_MEDICAMENT_CHOICES, null=True, blank=True)

    def __str__(self):
        return f'{self.nom} {self.dosage_form} {self.dosage} {self.unitdosage}'


class MouvementStock(models.Model):
    medicament = models.ForeignKey('Medicament', on_delete=models.CASCADE)
    patient = models.ForeignKey('core.Patient', on_delete=models.SET_NULL, null=True, blank=True)
    quantite = models.PositiveIntegerField()
    type_mouvement = models.CharField(max_length=50, choices=[('Entrée', 'Entrée'), ('Sortie', 'Sortie')])
    date_mouvement = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.type_mouvement == 'Sortie' and self.quantite > self.medicament.stock:
            raise ValidationError('La quantité retirée dépasse le stock disponible.')


@receiver(post_save, sender=MouvementStock)
def update_stock_on_save(sender, instance, **kwargs):
    if instance.medicament.stock is None:
        instance.medicament.stock = 0  # Initialiser à 0 si stock est None

    if instance.type_mouvement == 'Entrée':
        instance.medicament.stock += instance.quantite
    elif instance.type_mouvement == 'Sortie':
        instance.medicament.stock -= instance.quantite

    instance.medicament.save()


@receiver(post_delete, sender=MouvementStock)
def update_stock_on_delete(sender, instance, **kwargs):
    if instance.type_mouvement == 'Entrée':
        instance.medicament.stock -= instance.quantite
    elif instance.type_mouvement == 'Sortie':
        instance.medicament.stock += instance.quantite
    instance.medicament.save()

    def __str__(self):
        return f"{self.type_mouvement} de {self.quantite} {self.medicament.nom}"


class StockAlert(models.Model):
    medication = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    niveau_critique = models.PositiveIntegerField()
    quantite_actuelle = models.PositiveIntegerField()
    alerte = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for {self.medication.nom}: {self.quantite_actuelle} remaining"


@receiver(post_save, sender=Medicament)
def create_or_update_stock_alert(sender, instance, **kwargs):
    niveau_critique = 10  # Par exemple, valeur par défaut pour l'alerte
    if instance.stock < niveau_critique:
        StockAlert.objects.update_or_create(
            medication=instance,
            defaults={
                'niveau_critique': niveau_critique,
                'quantite_actuelle': instance.stock,
                'alerte': True  # Correction du champ
            }
        )
    else:
        StockAlert.objects.filter(medication=instance).delete()


class ArticleCommande(models.Model):
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite_commandee = models.PositiveIntegerField()
    date_commande = models.DateField(auto_now_add=True)
    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, choices=[
        ('Commandé', 'Commandé'),
        ('Reçu', 'Reçu'),
        ('En attente', 'En attente')
    ])


class Commande(models.Model):
    # numero = models.PositiveIntegerField()
    numero = models.PositiveIntegerField(unique=True, blank=True, null=True)
    articles = models.ManyToManyField('ArticleCommande', related_name='commandes')
    date_commande = models.DateField()
    created_at = models.DateField(auto_now=True)
    statut = models.CharField(max_length=50, choices=[
        ('Commandé', 'Commandé'),
        ('Reçu', 'Reçu'),
        ('En attente', 'En attente')
    ])

    def save(self, *args, **kwargs):
        if not self.numero:
            # Générer un numéro basé sur l'année et un compteur unique
            last_commande = Commande.objects.filter(date_commande__year=now().year).order_by('numero').last()
            if last_commande:
                self.numero = last_commande.numero + 1
            else:
                self.numero = int(f"{now().year}0001")  # Commencer avec l'année et un compteur
        super().save(*args, **kwargs)

    def get_context_data(self, **kwargs):
        from smit.forms import ArticleCommandeFormSet
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['articles_formset'] = ArticleCommandeFormSet(self.request.POST)
        else:
            context['articles_formset'] = ArticleCommandeFormSet(queryset=ArticleCommande.objects.none())
        context['title'] = "Créer une nouvelle commande"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        articles_formset = context['articles_formset']
        if form.is_valid() and articles_formset.is_valid():
            self.object = form.save()
            articles = articles_formset.save(commit=False)
            for article in articles:
                article.save()
                self.object.articles.add(article)
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=[ 'numero'], name='unique_commande_medicament')
    #     ]

    def __str__(self):
        return f"{self.articles} de {self.date_commande}"

    def get_status_badge(self):
        status_badges = {
            'Commandé': 'badge-primary',
            'Reçu': 'badge-success',
            'En attente': 'badge-warning',
        }
        return f'<span class="badge {status_badges.get(self.statut, "badge-secondary")}">{self.statut}</span>'

    def get_absolute_url(self):
        return reverse('commande_detail', kwargs={'pk': self.pk})


class RendezVous(models.Model):
    patient = models.ForeignKey('core.Patient', on_delete=models.CASCADE)
    pharmacie = models.ForeignKey('Pharmacy', on_delete=models.SET_NULL, null=True, blank=True)
    medicaments = models.ForeignKey(Medicament, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey('core.Service', on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey('core.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    suivi = models.ForeignKey('smit.Suivi', on_delete=models.SET_NULL, related_name='suivierdv', null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    reason = models.CharField(max_length=255, default="Récupération des médicaments")
    status = models.CharField(max_length=50, choices=[
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Missed', 'Missed'),
    ], default='Scheduled')
    recurrence = models.CharField(max_length=20, choices=[
        ('None', 'None'),
        ('Weekly', 'Chaque semaine'),
        ('Biweekly', 'Chaque deux semaines'),
        ('Monthly', 'Chaque mois'),
        ('Bimonthly', 'Chaque deux mois'),
        ('trimonthly', 'Chaque trois mois'),
        ('semestrial', 'Chaque Semestre'),
    ], default='None')
    recurrence_end_date = models.DateField(null=True, blank=True, help_text="Date de fin de la récurrence")
    reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.Employee', on_delete=models.SET_NULL, null=True, related_name='created_by')
    updated_at = models.DateTimeField(auto_now=True)

    def create_recurrences(self):
        """
        Crée automatiquement des rendez-vous récurrents en fonction des règles de récurrence.
        Empêche la duplication des rendez-vous.
        """
        if self.recurrence != 'None' and self.recurrence_end_date:
            current_date = self.date
            recurrences = []

            while current_date < self.recurrence_end_date:
                # Calculer la prochaine date en fonction du type de récurrence
                if self.recurrence == 'Weekly':
                    current_date += timedelta(weeks=1)
                elif self.recurrence == 'Biweekly':
                    current_date += timedelta(weeks=2)
                elif self.recurrence == 'Monthly':
                    current_date += timedelta(weeks=4)
                elif self.recurrence == 'Bimonthly':
                    current_date += timedelta(weeks=8)
                elif self.recurrence == 'trimonthly':
                    current_date += timedelta(weeks=13)
                elif self.recurrence == 'semestrial':
                    current_date += timedelta(weeks=26)

                # Vérifier si un rendez-vous existe déjà pour cette date et heure
                if not RendezVous.objects.filter(
                        patient=self.patient,
                        pharmacie=self.pharmacie,
                        doctor=self.doctor,
                        date=current_date,
                        time=self.time
                ).exists():
                    recurrences.append(
                        RendezVous(
                            patient=self.patient,
                            pharmacie=self.pharmacie,
                            suivi=self.suivi,
                            medicaments=self.medicaments,
                            service=self.service,
                            doctor=self.doctor,
                            date=current_date,
                            time=self.time,
                            reason=self.reason,
                            status='Scheduled',
                            recurrence='None',  # Les occurrences créées ne doivent pas être récurrentes
                            created_by=self.created_by,
                        )
                    )

            # Créer les rendez-vous en masse pour une meilleure efficacité
            if recurrences:
                RendezVous.objects.bulk_create(recurrences)

    def save(self, *args, **kwargs):
        if self.recurrence != 'None' and self.recurrence_end_date:
            self.create_recurrences()
        # Prevent overlapping appointments for the same patient and pharmacy
        overlapping = RendezVous.objects.filter(
            patient=self.patient,
            pharmacie=self.pharmacie,
            date=self.date,
            time=self.time
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("Un rendez-vous existe déjà pour ce patient à cette date et heure.")

        # Automatically mark appointments as missed if the date is in the past and not completed
        if self.date < timezone.now().date() and self.status == 'Scheduled':
            self.status = 'Missed'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rendez-vous de {self.patient} - {self.date} à {self.time}"


class Fournisseur(models.Model):
    nom = models.CharField(max_length=255, unique=True)
    adresse = models.TextField()
    contact = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return f"{self.nom}"
