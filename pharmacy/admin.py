from django.contrib import admin

from core.models import Location
from pharmacy.models import RendezVous, Medicament, MouvementStock, CathegorieMolecule, Molecule, Commande, \
    ArticleCommande, RendezVous, Fournisseur, Pharmacy


# Register your models here.


# @admin.register(RendezVous)
# class RendezVousAdmin(admin.ModelAdmin):
#     list_display = ("patient", "service", "date")
#     list_filter = ("patient", "date")
#     search_fields = ("patient", "date",)


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'stock', 'dosage', 'dosage_form', 'categorie', 'date_expiration')
    search_fields = ('nom', 'codebarre')
    list_filter = ('categorie', 'date_expiration', 'dosage_form')
    ordering = ('-date_expiration',)


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'quantite', 'type_mouvement', 'date_mouvement')
    search_fields = ('medicament__nom',)
    list_filter = ('type_mouvement', 'date_mouvement')


@admin.register(CathegorieMolecule)
class CathegorieMoleculeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom',)


@admin.register(Molecule)
class MoleculeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'cathegorie')
    search_fields = ('nom', 'cathegorie__nom')


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('numero', 'articles', 'date_commande')
    search_fields = ('articles', 'fournisseur__nom')
    # list_filter = ('statut', 'date_commande')


@admin.register(ArticleCommande)
class ArticleCommandeAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'quantite_commandee', 'date_commande','fournisseur')
    # search_fields = ('commande__id', 'medicament__nom')
    # list_filter = ('commande',)


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date', 'time', 'doctor', 'status')
    search_fields = ('patient__nom', 'doctor__nom')
    list_filter = ('status', 'date', 'recurrence')


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact', 'email', 'adresse')
    search_fields = ('nom', 'email')


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type', 'lieu', 'responsable')
