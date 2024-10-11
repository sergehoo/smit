from django.contrib import admin

from core.models import Location
from pharmacy.models import RendezVous


# Register your models here.


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):

    list_display = ("patient", "service", "date")
    list_filter = ("patient", "date")
    search_fields = ("patient", "date",)
