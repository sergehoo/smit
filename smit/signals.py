from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.http import request
from django.utils.timezone import now

from core.models import Patient
from smit.models import Service, ServiceSubActivity, SigneFonctionnel, Hospitalization


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



# @receiver(post_migrate)
# def add_default_signes_fonctionnels(sender, **kwargs):
#     signes_fonctionnels = [
#         'Douleure abdominales',
#         'Douleur thoraciques',
#         'Fièvre',
#         'Dyspnée',
#         'Toux sèche',
#         'Toux grasse',
#         'Fatigue',
#         'Dispnée',
#         'Expectorations',
#         'Hémoptysie',
#         'Nausées',
#         'Insommnie',
#         'Hypersonnie',
#         'Purit cutané',
#         'Purit vaginal',
#         'Ecoulement vaginal',
#         'Asthénie',
#         'Brûlures mictionnelles',
#         'vomissements',
#         'Perte d’appétit',
#         'Perte de connaissance ',
#         'Dysphagie',
#         'Convulsions',
#         'Constipation',
#         'Diarrhée',
#         'Oligurie',
#         'Anurie',
#         'Vertiges',
#         'Céphalées',
#         'Palpitations',
#         'Paresthésies',
#         'Troubles du sommeil',
#         'Saignements',
#         'Ictère',
#         'Otalgie',
#         'Otorrhée',
#         'Rhinorrhée',
#         'Œdèmes',
#         'Épistaxis antérieure',
#         'Épistaxis postérieure ',
#         'Conjonctives ',
#         'Etat de conscience '
#     ]
#
#     for signe in signes_fonctionnels:
#         SigneFonctionnel.objects.get_or_create(nom=signe)
