from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Patient
from smit.models import Service, ServiceSubActivity


@receiver(post_save, sender=Service)
def create_subservices(sender, instance, created, **kwargs):
    if created:
        # Liste des sous-services par défaut à créer pour chaque service
        default_subservices = [
            {'nom': 'Overview', 'icon': 'fa-solid fa-chart-line'},
            {'nom': 'Consultation', 'icon': 'fa-solid fa-stethoscope'},
            {'nom': 'Hospitalisation', 'icon': 'fa-solid fa-bed-pulse'},
            {'nom': 'Suivi', 'icon': 'fa-solid fa-person-walking-arrow-loop-left'},
            # Ajoutez d'autres sous-services par défaut si nécessaire
        ]

        for subservice in default_subservices:
            ServiceSubActivity.objects.create(service=instance, nom=subservice['nom'], icon=subservice['icon'])


@receiver(post_save, sender=Patient)
def create_user_for_patient(sender, instance, created, **kwargs):
    if created and not instance.user:
        # Générer un nom d'utilisateur unique
        username = f"{instance.nom.lower()}"
        if User.objects.filter(username=username).exists():
            username = f"{username}.{instance.generate_numeric_uuid()}"  # Ajouter un UUID pour éviter les doublons

        # Créer l'utilisateur
        user = User.objects.create(
            username=username,
            first_name=instance.prenoms,
            last_name=instance.nom,
            email=f"{username}@example.com"  # Remplacer par une adresse email valide si nécessaire
        )
        user.set_password(User.objects.make_random_password())  # Générer un mot de passe aléatoire
        user.save()

        # Associer l'utilisateur au patient
        instance.user = user
        instance.save()
