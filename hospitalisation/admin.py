from django.contrib import admin

from core.models import CasContact
from pharmacy.models import Medocsprescrits
from smit.models import UniteHospitalisation, ChambreHospitalisation, BoxHospitalisation, LitHospitalisation, \
    TypeAntecedent, SigneFonctionnel, HospitalizationIndicators, PrescriptionExecution, Observation, HistoriqueMaladie, \
    ParaclinicalExam, AntecedentsMedicaux, ModeDeVie, ModeDeVieCategorie, AppareilType, Appareil, ResumeSyndromique, \
    ProblemePose, TypeBilanParaclinique, ExamenStandard, BilanParaclinique, TypeImagerie, ImagerieMedicale


# Register your models here.


@admin.register(TypeAntecedent)
class TypeAntecedentAdmin(admin.ModelAdmin):
    list_display = (['nom', 'parent'])


@admin.register(ModeDeVieCategorie)
class ModeDeVieCategorieAdmin(admin.ModelAdmin):
    list_display = (['nom'])


@admin.register(ModeDeVie)
class ModeDeVieAdmin(admin.ModelAdmin):
    list_display = (['patient', 'hospitalisation', 'categorie', 'description'])


@admin.register(AppareilType)
class AppareilTypeAdmin(admin.ModelAdmin):
    list_display = (['nom'])


@admin.register(Appareil)
class AppareilAdmin(admin.ModelAdmin):
    list_display = (['type_appareil', 'nom', 'etat', 'observation'])


@admin.register(ResumeSyndromique)
class ResumeSyndromiqueAdmin(admin.ModelAdmin):
    list_display = ('patient', 'hospitalisation', 'created_by', 'created_at')
    list_filter = ('created_at', 'patient', 'created_by')
    search_fields = ('patient__nom', 'description', 'created_by__nom')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


@admin.register(ProblemePose)
class ProblemePoseAdmin(admin.ModelAdmin):
    list_display = ('patient', 'hospitalisation', 'created_by', 'created_at')
    list_filter = ('created_at', 'patient', 'created_by')
    search_fields = ('patient__nom', 'description', 'created_by__nom')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


@admin.register(AntecedentsMedicaux)
class AllergiesAdmin(admin.ModelAdmin):
    list_display = (['nom', 'type', 'patient'])


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
    list_display = ['prescription',
                    'scheduled_time',
                    'executed_at',
                    'executed_by',
                    'status'
                    ]


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
    search_fields = ('patient__nom', 'contact_patient__nom',)


@admin.register(Medocsprescrits)
class MedocsprescritsAdmin(admin.ModelAdmin):
    list_display = ('nom', 'dosage', 'unitdosage', 'dosage_form')
    search_fields = ('nom', 'dosage_form',)


@admin.register(ParaclinicalExam)
class ParaclinicalExamAdmin(admin.ModelAdmin):
    list_display = ('patient', 'exam_type', 'exam_name', 'prescribed_at', 'performed_at', "iteration", 'status')
    list_filter = ('exam_type', 'exam_name', 'status', 'prescribed_at')
    search_fields = ('patient__nom', 'exam_name', 'exam_type',)
    ordering = ('-prescribed_at',)
    date_hierarchy = 'prescribed_at'
    fieldsets = (
        ("Informations Générales", {
            "fields": ("patient", "hospitalisation", "exam_type", 'exam_name', "status", "iteration")
        }),
        ("Détails de l'Examen", {
            "fields": ("prescribed_at", "performed_at", "result_value", "result_text", 'created_by', "result_file")
        }),
    )

    def get_queryset(self, request):
        """Personnaliser la récupération des données."""
        qs = super().get_queryset(request)
        return qs.select_related("patient", "hospitalisation")


@admin.register(TypeBilanParaclinique)
class TypeBilanParacliniqueAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(ExamenStandard)
class ExamenStandardAdmin(admin.ModelAdmin):
    list_display = ("nom", "type_examen")
    search_fields = ("nom", "type_examen__nom")
    list_filter = ("type_examen",)


@admin.register(BilanParaclinique)
class BilanParacliniqueAdmin(admin.ModelAdmin):
    list_display = ("patient", "examen", "status", "doctor", "result", "result_date")
    search_fields = ("patient__nom", "examen__nom", "doctor__nom")
    list_filter = ("status", "examen__type_examen")

@admin.register(TypeImagerie)
class TypeImagerieAdmin(admin.ModelAdmin):
    list_display = ("nom",)

@admin.register(ImagerieMedicale)
class ImagerieMedicaleAdmin(admin.ModelAdmin):
    list_display = ("patient", "type_imagerie", "status", "date_examen", "radiologue")
    list_filter = ("status", "type_imagerie")
    search_fields = ("patient__nom", "radiologue__username")