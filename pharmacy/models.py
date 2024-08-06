from django.db import models
from schedule.models import Calendar, Event

from core.models import Patient, Service, Employee


class CathegorieMolecule(models.Model):
    nom = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nom


class Molecule(models.Model):
    nom = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cathegorie = models.ForeignKey(CathegorieMolecule, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nom


class Medicament(models.Model):
    nom = models.CharField(max_length=255)
    description = models.TextField()
    stock = models.PositiveIntegerField()
    date_expiration = models.DateField()
    categorie = models.ForeignKey(CathegorieMolecule, on_delete=models.SET_NULL, null=True, blank=True)
    fournisseur = models.ForeignKey('Fournisseur', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.nom}--{self.categorie}--{self.fournisseur}'


class MouvementStock(models.Model):
    medicament = models.ForeignKey('Medicament', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    type_mouvement = models.CharField(max_length=50, choices=[('Entrée', 'Entrée'), ('Sortie', 'Sortie')])
    date_mouvement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_mouvement} de {self.quantite} {self.medicament.nom}"


class StockAlert(models.Model):
    medication = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    niveau_critique = models.PositiveIntegerField()
    quantité_actuelle = models.PositiveIntegerField()
    alerté = models.BooleanField(default=False)


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
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='rdvcreator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Fournisseur(models.Model):
    nom = models.CharField(max_length=255)
    adresse = models.TextField()
    contact = models.CharField(max_length=255)
    email = models.EmailField()
