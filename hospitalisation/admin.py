from django.contrib import admin

from core.models import CasContact
from smit.models import UniteHospitalisation, ChambreHospitalisation, BoxHospitalisation, LitHospitalisation, \
    TypeAntecedent, SigneFonctionnel, HospitalizationIndicators, PrescriptionExecution, Observation, HistoriqueMaladie


# Register your models here.


@admin.register(TypeAntecedent)
class TypeAntecedentAdmin(admin.ModelAdmin):
    list_display = (['nom'])


@admin.register(HospitalizationIndicators)
class HospitalizationIndicatorsAdmin(admin.ModelAdmin):
    list_display = (['hospitalisation'])


# Pré-enregistrement des types d'antécédents s'ils n'existent pas déjà
# def add_default_antecedents():
#     antecedents_type = [
#         'Antécédents médicaux personnels',
#         'Antécédents familiaux',
#         'Antécédents chirurgicaux',
#         'Antécédents gynécologiques et obstétricaux',
#         'Antécédents médicamenteux',
#         'Antécédents psychologiques',
#         'Antécédents sociaux',
#         'Antécédents obstétricaux'
#     ]
#
#     for antecedent in antecedents_type:
#         if not TypeAntecedent.objects.filter(nom=antecedent).exists():
#             TypeAntecedent.objects.create(nom=antecedent)


# Appeler la fonction lors du démarrage de l'administration
# add_default_antecedents()


@admin.register(UniteHospitalisation)
class UniteHospitalisationAdmin(admin.ModelAdmin):
    list_display = ['nom']


class BoxHospitalisationAdmin(admin.TabularInline):
    list_display = ['nom', 'capacite', 'occuper']
    model = BoxHospitalisation


@admin.register(ChambreHospitalisation)
class ChambreHospitalisation(admin.ModelAdmin):
    list_display = ['nom', 'unite']
    inlines = [BoxHospitalisationAdmin]


@admin.register(LitHospitalisation)
class LitHospitalisation(admin.ModelAdmin):
    list_display = (['nom', 'box', 'occuper', 'occupant', 'reserved',
                     'is_out_of_service',
                     'is_cleaning',
                     'status_changed_at'])


@admin.register(SigneFonctionnel)
class SigneFonctionnelAdmin(admin.ModelAdmin):
    list_display = (['nom', 'hospitalisation'])


@admin.register(PrescriptionExecution)
class PrescriptionExecutionAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'scheduled_time']


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_enregistrement', 'statut')
    search_fields = ('patient__nom', 'details', 'statut')
    list_filter = ('statut', 'date_enregistrement')


@admin.register(HistoriqueMaladie)
class HistoriqueMaladieAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_enregistrement',)
    search_fields = ('patient__nom', 'details', 'statut')


@admin.register(CasContact)
class CaseContactAdmin(admin.ModelAdmin):
    list_display = ('patient', 'contact_person', 'relationship')
    search_fields = ('patient__nom', 'contact_patient__nom', )
