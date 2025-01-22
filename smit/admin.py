from django.contrib import admin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from core.models import Location, PolesRegionaux, HealthRegion, DistrictSanitaire, Maladie
from laboratory.models import Echantillon
from pharmacy.models import CathegorieMolecule, Medicament
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    ServiceSubActivity, Consultation, Protocole, Evaluation, Molecule, Allergies, \
    AntecedentsMedicaux, Symptomes, Analyse, Examen, Hospitalization, TestRapideVIH, EnqueteVih, MaladieOpportuniste, \
    Suivi, Prescription, SigneFonctionnel, IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, \
    ComplicationsIndicators, EffetIndesirable, AvisMedical, Diagnostic, Observation, HistoriqueMaladie, Vaccination, \
    Comorbidite, InfectionOpportuniste, TraitementARV, TypeProtocole, SuiviProtocole

# Register your models here.
admin.site.site_header = 'SERVICE DES MALADIES INFESTIEUSE ET TROPICALES | BACK-END CONTROLER'
admin.site.site_title = 'SMIT Super Admin Pannel'
admin.site.site_url = 'http://smitci.com/'
admin.site.index_title = 'SMIT'
admin.empty_value_display = '**Empty**'


@admin.register(Echantillon)
class EchantillonAdmin(admin.ModelAdmin):
    pass


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    pass


# @admin.register(EmployeeEmployee)
# class EmployeeAdmin(admin.ModelAdmin):
#     pass


@admin.register(Constante)
class ConstanteAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'created_at', 'hospitalisation']


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('numeros', 'patient', 'doctor', 'consultation_date', 'status')
    list_filter = ('status', 'consultation_date')
    search_fields = ('numeros', 'patient__nom', 'doctor__user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ServiceSubActivity)
class ServiceSubActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(TypeProtocole)
class TypeProtocoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'parent')


@admin.register(Protocole)
class ProtocoleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_protocole', 'date_debut', 'date_fin', 'duree')
    search_fields = ('nom', 'patient__nom', 'type_protocole__nom')
    list_filter = ('type_protocole',)


@admin.register(SuiviProtocole)
class SuiviProtocoleAdmin(admin.ModelAdmin):
    list_display = (
        'protocole',
        'suivi',
        'date_debut',
        'date_fin',
        'created_at',
        'created_by',
    )


# Configuration pour le modèle TraitementARV
@admin.register(TraitementARV)
class TraitementARVAdmin(admin.ModelAdmin):
    list_display = ('nom', 'patient', 'type_traitement', 'date_creation', 'duree_traitement')
    search_fields = ('nom', 'patient__nom', 'patient__prenom')
    list_filter = ('type_traitement', 'date_creation')


# Configuration pour le modèle InfectionOpportuniste
@admin.register(InfectionOpportuniste)
class InfectionOpportunisteAdmin(admin.ModelAdmin):
    list_display = ('type_infection', 'patient', 'date_diagnostic', 'gravite', 'statut_traitement')
    search_fields = ('type_infection', 'patient__nom', 'patient__prenom')
    list_filter = ('gravite', 'statut_traitement', 'date_diagnostic')
    date_hierarchy = 'date_diagnostic'


# Configuration pour le modèle Comorbidite
@admin.register(Comorbidite)
class ComorbiditeAdmin(admin.ModelAdmin):
    list_display = ('type_comorbidite', 'patient', 'date_diagnostic', 'statut_traitement')
    search_fields = ('type_comorbidite', 'patient__nom', 'patient__prenom')
    list_filter = ('statut_traitement', 'date_diagnostic')
    date_hierarchy = 'date_diagnostic'


# Configuration pour le modèle Vaccination
@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ('type_vaccin', 'patient', 'date_administration', 'rappel_necessaire', 'centre_vaccination')
    search_fields = ('type_vaccin', 'patient__nom', 'patient__prenom', 'centre_vaccination')
    list_filter = ('rappel_necessaire', 'date_administration')
    date_hierarchy = 'date_administration'


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    pass


@admin.register(Allergies)
class AllergiesAdmin(admin.ModelAdmin):
    pass


@admin.register(AntecedentsMedicaux)
class AllergiesAdmin(admin.ModelAdmin):
    pass


@admin.register(Symptomes)
class AllergiesAdmin(admin.ModelAdmin):
    pass


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'patients_requested', 'analyses', 'date', 'accepted', 'created_at')
    list_filter = ('date', 'accepted')
    search_fields = ('request_number', 'patients_requested__name',
                     'analyses__name')  # Assuming patients_requested and analyses have a name field.
    ordering = ('-created_at',)
    autocomplete_fields = ('patients_requested', 'analyses')  # For better usability with ForeignKey fields.


@admin.register(Analyse)
class AnalyseAdmin(admin.ModelAdmin):
    list_display = ('name', 'tarif_base', 'tarif_public', 'tarif_mutuelle', 'forfait_assurance', 'result')
    list_filter = ('tarif_base',)
    search_fields = ('name',)
    ordering = ('name',)
    fields = (
        'name', 'tarif_base', 'tarif_public', 'tarif_mutuelle', 'forfait_assurance', 'forfait_societe',
        'lanema', 'analysis_description', 'analysis_method', 'delai_analyse', 'result', 'notes'
    )
    readonly_fields = ('tarif_public', 'tarif_mutuelle', 'forfait_assurance', 'forfait_societe', 'lanema')


@admin.register(Hospitalization)
class HospitalizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'medication']


@admin.register(ComplicationsIndicators)
class ComplicationsIndicatorsAdmin(admin.ModelAdmin):
    list_display = ['id', 'hospitalisation']


@admin.register(IndicateurBiologique)
class IndicateurBiologiqueAdmin(admin.ModelAdmin):
    list_display = ['id', 'hospitalisation']


@admin.register(IndicateurFonctionnel)
class IndicateurFonctionnelAdmin(admin.ModelAdmin):
    list_display = ['id', 'hospitalisation']


@admin.register(IndicateurSubjectif)
class IndicateurSubjectifAdmin(admin.ModelAdmin):
    list_display = ['id', 'hospitalisation']


@admin.register(Suivi)
class SuiviAdmin(admin.ModelAdmin):
    list_display = ('patient', 'services', 'date_suivi', 'statut_patient', 'adherence_traitement')
    search_fields = ('patient__nom', 'patient__prenoms', 'services__nom')
    list_filter = ('statut_patient', 'adherence_traitement', 'date_suivi', 'mode')
    date_hierarchy = 'date_suivi'
    ordering = ('-date_suivi',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations générales', {
            'fields': ('patient', 'services', 'activite', 'mode', 'date_suivi')
        }),
        ('Détails du suivi', {
            'fields': ('statut_patient', 'adherence_traitement', 'poids', 'cd4', 'charge_virale', 'observations')
        }),
        ('Rendez-vous', {
            'fields': ('rdvconsult', 'rdvpharmacie')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# @admin.register(Localite)
# class LocaliteAdmin(admin.ModelAdmin):
#     list_display = ('nom', 'code', 'type', 'region')
#     search_fields = ('nom',)


class EmployeeResource(resources.ModelResource):
    def before_import_row(self, row, **kwargs):
        # Créer l'utilisateur s'il n'existe pas
        username = row.get('user_username')
        email = row.get('user_email')
        first_name = row.get('user_first_name')
        last_name = row.get('user_last_name')
        default_password = 'defaultpassword123'  # Définissez votre mot de passe par défaut ici

        user, created = User.objects.get_or_create(username=username, defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        })
        if created:
            user.set_password(default_password)
            user.save()

        row['user'] = user.id

    class Meta:
        model = Employee
        import_id_fields = ('qlook_id',)  # Remplacez par le champ de votre choix
        fields = ('qlook_id', 'user', 'gender', 'situation_matrimoniale', 'nbr_enfants', 'persone_ref_noms',
                  'persone_ref_contact', 'num_cnps', 'phone', 'bank_name', 'account_number', 'code_guichet', 'cle_rib',
                  'code_banque', 'iban', 'swift', 'bank_adress', 'alternative_phone', 'nationalite', 'personal_mail',
                  'birthdate', 'date_embauche', 'end_date', 'salary', 'dpt', 'job_title', 'phone_number', 'photo',
                  'sortie', 'is_deleted', 'slug', 'created_at')


class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = ['qlook_id', 'user', 'gender', ]
    search_fields = ['qlook_id', 'user__username']


admin.site.register(Employee, EmployeeAdmin)


class PatientResource(resources.ModelResource):

    def before_import_row(self, row, **kwargs):
        # Créer l'utilisateur s'il n'existe pas
        username = row.get('user_username')
        email = row.get('user_email')
        first_name = row.get('user_first_name')
        last_name = row.get('user_last_name')
        default_password = 'defaultpassword123'  # Définissez votre mot de passe par défaut ici

        user, created = User.objects.get_or_create(username=username, defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        })
        if created:
            user.set_password(default_password)
            user.save()

        row['user'] = user.id

    class Meta:
        model = Patient
        import_id_fields = ('code_patient',)  # Remplacez par le champ de votre choix
        fields = ('user', 'code_patient', 'code_vih', 'nom', 'prenoms', 'contact', 'situation_matrimoniale',
                  'lieu_naissance', 'date_naissance', 'genre', 'nationalite', 'profession', 'nbr_enfants',
                  'groupe_sanguin', 'niveau_etude', 'employeur', 'created_by', 'avatar', 'localite', 'status')


@admin.register(Patient)
class PatientAdmin(ImportExportModelAdmin):
    resource_class = PatientResource
    list_display = ('code_patient', 'code_vih', 'nom', 'prenoms')
    search_fields = ['code_patient', 'nom']


class TestRapideVIHAdmin(ImportExportModelAdmin):
    pass
    # resource_class = PatientResource


admin.site.register(TestRapideVIH, TestRapideVIHAdmin)


class EnqueteVihAdmin(ImportExportModelAdmin):
    pass
    # resource_class = PatientResource


admin.site.register(EnqueteVih, EnqueteVihAdmin)


class MaladieOpportunisteAdmin(ImportExportModelAdmin):
    pass
    # resource_class = PatientResource


admin.site.register(MaladieOpportuniste, MaladieOpportunisteAdmin)


@admin.register(PolesRegionaux)
class PolesRegionauxAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')  # Affiche les colonnes ID et nom
    search_fields = ('name',)  # Ajoute une barre de recherche pour le champ 'name'


@admin.register(HealthRegion)
class HealthRegionDistrictAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name', 'poles')  # Affiche ID, nom et pole associé
    search_fields = ('name', 'poles__name')  # Barre de recherche sur 'name' et le nom du pole
    list_filter = ('poles',)  # Ajoute un filtre par pole régional


@admin.register(DistrictSanitaire)
class DistrictSanitaireAdmin(ImportExportModelAdmin):
    list_display = ('id', 'nom', 'region', 'previous_rank')  # Colonnes principales à afficher
    search_fields = ('nom', 'region__name')  # Recherche par nom du district ou de la région
    list_filter = ('region',)  # Filtrage par région de santé
    ordering = ('previous_rank',)  # Trie par classement précédent
    readonly_fields = ('geojson',)  # Rendre le champ 'geojson' en lecture seule dans l'admin
    fieldsets = (
        (None, {
            'fields': ('nom', 'region', 'previous_rank')
        }),
        ('Données géographiques', {
            'fields': ('geojson',),
            'classes': ('collapse',),  # Permet de cacher la section
        }),
    )


@admin.register(Location)
class LocationAdmin(ImportExportModelAdmin):
    list_display = ('name', 'type', 'population', 'district')  # Colonnes affichées dans la liste
    search_fields = ('name', 'district__nom')  # Recherche par nom et district
    list_filter = ('type', 'district')  # Filtres par type et district
    ordering = ('name',)  # Tri par nom
    fieldsets = (
        (None, {
            'fields': ('name', 'type', 'population', 'source', 'district')
        }),
    )


@admin.register(EffetIndesirable)
class EffetIndesirableAdmin(admin.ModelAdmin):
    list_display = (
        'hospitalisation', 'patient', 'gravite', 'date_apparition', 'date_signalement', 'medicament_associe')
    list_filter = ('gravite', 'date_apparition', 'medecin')
    search_fields = ('description', 'patient__nom', 'patient__prenom')


@admin.register(AvisMedical)
class AvisMedicalAdmin(admin.ModelAdmin):
    list_display = ('titre', 'hospitalisation', 'medecin', 'date_avis', 'mise_a_jour')
    list_filter = ('date_avis', 'mise_a_jour', 'medecin')
    search_fields = ('titre', 'contenu', 'hospitalisation__patient__nom', 'hospitalisation__patient__prenom')


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ('type_diagnostic', 'hospitalisation', 'date_diagnostic', 'maladie', 'medecin_responsable')
    list_filter = ('type_diagnostic', 'date_diagnostic')
    search_fields = ('hospitalisation__patient__nom', 'hospitalisation__patient__prenom')


@admin.register(Maladie)
class MaladieAdmin(admin.ModelAdmin):
    list_display = ('code_cim','nom', 'categorie', 'gravite', 'date_diagnostic', 'medecin_responsable')
    search_fields = ('code_cim','nom', 'categorie', 'patient__nom')
    list_filter = ('categorie', 'gravite', 'date_diagnostic')
