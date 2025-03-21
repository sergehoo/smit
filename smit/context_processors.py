from datetime import date

from core.models import Patient
from smit.models import Service, Appointment, Hospitalization, Consultation, Suivi, BilanParaclinique


def services_processor(request):
    services = Service.objects.all()
    services = Service.objects.all()

    return {'services': services, }


def menu_processor(request):
    today = date.today()
    appointments_today = Appointment.objects.filter(date=today, status='Scheduled').count()
    patient_nbr = Patient.objects.all().count()
    appointments_all = Appointment.objects.all().count()
    examens = BilanParaclinique.objects.filter(result=None).count()
    examensdone = BilanParaclinique.objects.filter(result__isnull=False).count()
    urgencehospi = Patient.objects.filter(urgence=True).count()


    hospitalized_count = Hospitalization.objects.filter(discharge_date__isnull=True).count()
    discharged_count = Hospitalization.objects.filter(discharge_date__isnull=False).count()
    consultations = Consultation.objects.all().count()
    suivi = Suivi.objects.all().count()
    # vih_consult = Consultation.objects.filter(service='VIH-SIDA').count()

    return {'apointments_nbr': appointments_today,
            'patient_nbr': patient_nbr,
            'appointments_all': appointments_all,
            'Hospitaliza_encours': hospitalized_count,
            'discharged_count': discharged_count,
            'consul_nbr': consultations,
            'suivi_nbr': suivi,
            'examencount': examens,
            'urgencehospi': urgencehospi,
            'examensdonecount': examensdone
            }

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
