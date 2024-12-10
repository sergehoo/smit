from django.contrib import admin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from core.models import Location, PolesRegionaux, HealthRegion, DistrictSanitaire
from laboratory.models import Echantillon
from pharmacy.models import CathegorieMolecule, Medicament
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    ServiceSubActivity, Consultation, EtapeProtocole, Protocole, Evaluation, Molecule, Allergies, \
    AntecedentsMedicaux, Symptomes, Analyse, Examen, Hospitalization, TestRapideVIH, EnqueteVih, MaladieOpportuniste, \
    Suivi, Prescription, SigneFonctionnel, IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, \
    ComplicationsIndicators


# Register your models here.


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


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
    list_display = ['patient', 'services', 'hospitalised']


@admin.register(ServiceSubActivity)
class ServiceSubActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(EtapeProtocole)
class EtapeProtocoleAdmin(admin.ModelAdmin):
    pass


@admin.register(Protocole)
class ProtocoleAdmin(admin.ModelAdmin):
    pass


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    pass


@admin.register(CathegorieMolecule)
class CathegorieMoleculeAdmin(admin.ModelAdmin):
    pass


@admin.register(Molecule)
class MoleculeAdmin(admin.ModelAdmin):
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


@admin.register(Analyse)
class AnalyseAdmin(admin.ModelAdmin):
    pass


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    pass


@admin.register(Hospitalization)
class HospitalizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient']


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'dosage_form', 'dosage', 'unitdosage', 'fournisseur', 'categorie']
    # list_editable = ['dosage']
    # list_display_links = ['fournisseur']


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
    list_display = ['activite']


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
