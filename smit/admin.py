from django.contrib import admin

from core.models import Location
from pharmacy.models import CathegorieMolecule, Medicament
from smit.models import Patient, Appointment, Service, Employee, Constante, \
    ServiceSubActivity, Consultation, EtapeProtocole, Protocole, Evaluation, Molecule, Allergies, \
    AntecedentsMedicaux, Symptomes, Analyse, Examen, Hospitalization


# Register your models here.
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    pass


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    pass


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    pass


@admin.register(Constante)
class ConstanteAdmin(admin.ModelAdmin):
    pass


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



