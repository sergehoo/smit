from datetime import date

from django.core.cache import cache
from core.models import Patient
from smit.models import Service, Appointment, Hospitalization, Consultation, Suivi, BilanParaclinique, BilanInitial


# def check_accueil_group(request):
#     is_accueil = False
#     if request.user.is_authenticated:
#         accueil_group = Group.objects.get(name='accueil')  # Assurez-vous que le nom du groupe est correct
#         is_accueil = accueil_group in request.user.groups.all()
#     return {'is_accueil': is_accueil}
#
#
# def check_facturation_group(request):
#     is_facturation = False
#     if request.user.is_authenticated:
#         employee_group = Group.objects.get(name='facturation')  # Assurez-vous que le nom du groupe est correct
#         is_facturation = employee_group in request.user.groups.all()
#     return {'is_facturation': is_facturation}
#
#
# def check_logistique_group(request):
#     is_logistique = False
#     if request.user.is_authenticated:
#         logistique_group = Group.objects.get(name='logistique')  # Assurez-vous que le nom du groupe est correct
#         is_logistique = logistique_group in request.user.groups.all()
#     return {'is_logistique': is_logistique}


#
#
# def check_prelevement_group(request):
#     is_prelevement = False
#     if request.user.is_authenticated:
#         prelevement_group = Group.objects.get(name='prelevement')  # Assurez-vous que le nom du groupe est correct
#         is_prelevement = prelevement_group in request.user.groups.all()
#     return {'is_prelevement': is_prelevement}


#
# #
# def check_laboratoire_group(request):
#     is_laboratoire = False
#     if request.user.is_authenticated:
#         laboratoire_group = Group.objects.get(name='laboratoire')  # Assurez-vous que le nom du groupe est correct
#         is_laboratoire = laboratoire_group in request.user.groups.all()
#     return {'is_laboratoire': is_laboratoire}
#

#
#
# def check_resultats_group(request):
#     is_resultats = False
#     if request.user.is_authenticated:
#         resultats_group = Group.objects.get(name='resultats')  # Assurez-vous que le nom du groupe est correct
#         is_resultats = resultats_group in request.user.groups.all()
#     return {'is_resultats': is_resultats}


def global_context(request):
    today = date.today()
    cache_key = 'menu_context'
    context = cache.get(cache_key)

    if not context:
        context = {
            'services': Service.objects.all(),
            'apointments_nbr': Appointment.objects.filter(date=today, status='Scheduled').count(),
            'patient_nbr': Patient.objects.count(),
            'appointments_all': Appointment.objects.count(),
            'Hospitaliza_encours': Hospitalization.objects.filter(discharge_date__isnull=True).count(),
            'discharged_count': Hospitalization.objects.filter(discharge_date__isnull=False).count(),
            'consul_nbr': Consultation.objects.count(),
            'suivi_nbr': Suivi.objects.count(),
            'examencount': BilanParaclinique.objects.filter(result=None).count(),
            'examensdonecount': BilanParaclinique.objects.filter(result__isnull=False).count(),
            'urgencehospi': Patient.objects.filter(urgence=True).count(),
            'bilaninitial': BilanInitial.objects.all().count(),
        }
        cache.set(cache_key, context, 60)  # Expire après 60 sec

    return context
