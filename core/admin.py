from django.contrib import admin
from django.urls import path
from django.utils.html import format_html

from core.models import VisitCounter
from core.views import dashboard_view


# Register your models here.
# #
# @admin.register(VisitCounter)
# class VisitCounterAdmin(admin.ModelAdmin):
#     list_display = ('ip_address', 'city', 'country', 'timestamp', 'device_type', 'get_map_url')
#     list_filter = ('country', 'is_mobile', 'is_tablet', 'is_pc')
#     search_fields = ('ip_address', 'city', 'country', 'isp')
#
#     def device_type(self, obj):
#         """Affiche le type d'appareil avec un badge de couleur"""
#         if obj.is_mobile:
#             return format_html('<span style="color: green;">📱 Mobile</span>')
#         elif obj.is_tablet:
#             return format_html('<span style="color: orange;">📟 Tablette</span>')
#         else:
#             return format_html('<span style="color: blue;">💻 PC</span>')
#
#     device_type.short_description = "Appareil"
#
#     def total_visits(self):
#         """Affiche le total des visites en gras"""
#         return format_html("<strong>{}</strong>", VisitCounter.objects.count())
#
#     total_visits.short_description = "Total des visites"
#
#     def dashboard_button(self):
#         return format_html('<a href="/admin/dashboard/" class="button">📊 Voir les Statistiques</a>')
#
#     dashboard_button.allow_tags = True
#     dashboard_button.short_description = "Tableau de Bord"
#
#
# class CustomAdminSite(admin.AdminSite):
#     """ Personnalisation de l'admin Django avec un tableau de bord """
#     site_header = "Administration Conférence d'Abidjan"
#     site_title = "Tableau de Bord"
#     index_title = "Bienvenue sur le Tableau de Bord"
#
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path("dashboard/", self.admin_view(dashboard_view), name="dashboard"),
#         ]
#         return custom_urls + urls
#
#     def dashboard_link(self):
#         return format_html('<a href="/admin/dashboard/" class="button">📊 Voir le tableau de bord</a>')
#
#     dashboard_link.allow_tags = True
#     dashboard_link.short_description = "Tableau de Bord"
#
#
# admin_site = CustomAdminSite(name="admin")
# # Enregistrer les modèles avec le nouvel admin
# admin_site.register(VisitCounter, VisitCounterAdmin)
#
# # Ajouter un panneau de statistiques dans l'admin
# admin.site.site_header = "Administration du site"
# admin.site.site_title = "Admin"
# admin.site.index_title = f"Total des visites : {VisitCounter.objects.count()}"
