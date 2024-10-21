from django.contrib import admin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from core.models import Location
from laboratory.models import Echantillon
from pharmacy.models import CathegorieMolecule, Medicament
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    ServiceSubActivity, Consultation, EtapeProtocole, Protocole, Evaluation, Molecule, Allergies, \
    AntecedentsMedicaux, Symptomes, Analyse, Examen, Hospitalization, TestRapideVIH, EnqueteVih, MaladieOpportuniste, \
    Suivi


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


# @admin.register(Employee)
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
    pass


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    pass


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
