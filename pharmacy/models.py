import random
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from schedule.models import Calendar, Event

from core.models import Patient, Service, Employee

FORME_MEDICAMENT_CHOICES = [
    ('Comprimé', 'Comprimé'),
    ('Sirop', 'Sirop'),
    ('Injection', 'Injection'),
    ('Gélule', 'Gélule'),
    ('Crème', 'Crème'),
    ('Pommade', 'Pommade'),
    ('Suppositoire', 'Suppositoire'),
    ('Gouttes', 'Gouttes'),
    ('Patch', 'Patch'),
    ('Inhalateur', 'Inhalateur'),
    ('Solution', 'Solution'),
    ('Suspension', 'Suspension'),
    ('Poudre', 'Poudre'),
    ('Spray', 'Spray'),
    ('Ovule', 'Ovule'),
    ('Collyre', 'Collyre'),  # pour les yeux
    ('Aérosol', 'Aérosol'),
    ('Élixir', 'Élixir'),
    ('Baume', 'Baume'),
    ('Granulé', 'Granulé'),
    ('Capsule', 'Capsule'),
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


class Medicament(models.Model):
    codebarre = models.CharField(max_length=150, unique=True, default=generate_unique_code_barre,
                                 help_text="Code unique pour le médicament", validators=[RegexValidator(regex=r'^\d{12}$',message="Le code-barre doit être composé de 12 chiffres.")])  # Pour l'identification par code-barre
    nom = models.CharField(max_length=255, null=True, blank=True, unique=True)
    dosage = models.IntegerField(null=True, blank=True)
    unitdosage = models.CharField(max_length=50, choices=UNITE_DOSAGE_CHOICES, null=True, blank=True,
                                  help_text="Ex: 500mg, 20mg/ml")
    dosage_form = models.CharField(max_length=50, choices=FORME_MEDICAMENT_CHOICES, null=True, blank=True)
    description = models.TextField(null=True, blank=True, )
    stock = models.PositiveIntegerField(null=True, blank=True, )
    date_expiration = models.DateField(null=True, blank=True, )
    categorie = models.ForeignKey(CathegorieMolecule, on_delete=models.SET_NULL, null=True, blank=True)
    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.SET_NULL, null=True, blank=True)
    molecules = models.ManyToManyField(Molecule)
    miniature = models.ImageField(upload_to="pharmacy/miniature", null=True, blank=True)

    def __str__(self):
        return f'{self.nom} {self.dosage_form} {self.dosage} {self.unitdosage}'


class MouvementStock(models.Model):
    medicament = models.ForeignKey('Medicament', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    type_mouvement = models.CharField(max_length=50, choices=[('Entrée', 'Entrée'), ('Sortie', 'Sortie')])
    date_mouvement = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.type_mouvement == 'Sortie' and self.quantite > self.medicament.stock:
            raise ValidationError('La quantité retirée dépasse le stock disponible.')


@receiver(post_save, sender=MouvementStock)
def update_stock_on_save(sender, instance, **kwargs):
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


@receiver(post_save, sender=Medicament)
def create_or_update_stock_alert(sender, instance, **kwargs):
    niveau_critique = 10  # Par exemple, valeur par défaut
    if instance.stock < niveau_critique:
        StockAlert.objects.update_or_create(
            medication=instance,
            defaults={
                'niveau_critique': niveau_critique,
                'quantité_actuelle': instance.stock,
                'alerté': True
            }
        )
    else:
        StockAlert.objects.filter(medication=instance).delete()


class Commande(models.Model):
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite_commandee = models.PositiveIntegerField()
    date_commande = models.DateField()
    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.CASCADE)
    statut = models.CharField(max_length=50, choices=[
        ('Commandé', 'Commandé'),
        ('Reçu', 'Reçu'),
        ('En attente', 'En attente')
    ])


class ArticleCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='articles')
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['commande', 'medicament'], name='unique_commande_medicament')
        ]

    def __str__(self):
        return f"{self.quantite} de {self.medicament.nom}"


class RendezVous(models.Model):
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
    recurrence = models.CharField(max_length=20, choices=[
        ('None', 'None'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Semi-Annual', 'Semi-Annual'),
        ('Annual', 'Annual')
    ], default='None')
    recurrence_end_date = models.DateField(null=True, blank=True, help_text="Date de fin de la récurrence")
    reminder = models.BooleanField(default=False)
    reminder_interval = models.CharField(max_length=20, choices=[
        ('None', 'None'),
        ('1 Day', '1 Day'),
        ('2 Days', '2 Days'),
        ('1 Week', '1 Week')
    ], default='None')
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='rdvcreator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if RendezVous.objects.filter(patient=self.patient, date=self.date, time=self.time).exists():
            raise ValidationError("Un rendez-vous existe déjà à cette date et heure pour ce patient.")
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
