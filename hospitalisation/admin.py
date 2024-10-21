from django.contrib import admin

from smit.models import UniteHospitalisation, ChambreHospitalisation, BoxHospitalisation, LitHospitalisation, \
    TypeAntecedent, SigneFonctionnel


# Register your models here.


@admin.register(TypeAntecedent)
class TypeAntecedentAdmin(admin.ModelAdmin):
    list_display = ['nom']


# Pré-enregistrement des types d'antécédents s'ils n'existent pas déjà
def add_default_antecedents():
    antecedents_type = [
        'Antécédents médicaux personnels',
        'Antécédents familiaux',
        'Antécédents chirurgicaux',
        'Antécédents gynécologiques et obstétricaux',
        'Antécédents médicamenteux',
        'Antécédents psychologiques',
        'Antécédents sociaux',
        'Antécédents obstétricaux'
    ]

    for antecedent in antecedents_type:
        if not TypeAntecedent.objects.filter(nom=antecedent).exists():
            TypeAntecedent.objects.create(nom=antecedent)


# Appeler la fonction lors du démarrage de l'administration
add_default_antecedents()


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
    list_display = (['nom', 'box', 'occuper', 'occupant'])


@admin.register(SigneFonctionnel)
class SigneFonctionnelAdmin(admin.ModelAdmin):
    list_display = ['nom', 'hospitalisation']
