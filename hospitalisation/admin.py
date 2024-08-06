from django.contrib import admin

from smit.models import UniteHospitalisation, ChambreHospitalisation, BoxHospitalisation, LitHospitalisation


# Register your models here.


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
    list_display = ['nom', 'box', 'occuper', 'occupant']

