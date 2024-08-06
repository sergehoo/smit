from django.db.models.signals import post_save
from django.dispatch import receiver

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