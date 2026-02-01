import csv
from datetime import timedelta, date

from axes.models import AccessAttempt
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.forms import forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from core.models import VisitCounter, VIHProfile, Patient
from core.views import dashboard_view


# Register your models here.
# @admin.register(VisitCounter)
# class VisitCounterAdmin(admin.ModelAdmin):
#     list_display = ('ip_address', 'city', 'country', 'timestamp', 'device_type', 'get_map_url')
#     list_filter = ('country', 'is_mobile', 'is_tablet', 'is_pc')
#     search_fields = ('ip_address', 'city', 'country', 'isp')
#
#     def device_type(self, obj):
#         if obj.is_mobile:
#             return format_html('<span style="color: green;">📱 Mobile</span>')
#         elif obj.is_tablet:
#             return format_html('<span style="color: orange;">📟 Tablette</span>')
#         return format_html('<span style="color: blue;">💻 PC</span>')
#
#     device_type.short_description = "Appareil"
class MyAdminSite(admin.AdminSite):
    site_header = "SMIT Admin"
    site_title = "SMIT Admin"

    def each_context(self, request):
        context = super().each_context(request)
        total_attempts = AccessAttempt.objects.count()
        context['axes_total_attempts'] = total_attempts
        return context

admin_site = MyAdminSite(name='myadmin')

class CustomAdminSite(admin.AdminSite):
    site_header = "Administration Conférence d'Abidjan"
    site_title = "Tableau de Bord"
    index_title = "Bienvenue sur le Tableau de Bord"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("dashboard/", self.admin_view(dashboard_view), name="dashboard"),
        ]
        return custom_urls + urls

    def dashboard_link(self):
        return format_html('<a href="/admin/dashboard/" class="button">📊 Voir le tableau de bord</a>')

    dashboard_link.short_description = "Tableau de Bord"


admin_site = CustomAdminSite(name="admin")
# admin_site.register(VisitCounter, VisitCounterAdmin)
admin.site.index_title = "Admin SMIT"
admin.site.site_header = "Administration du site"
admin.site.site_title = "Admin"
# admin.site.index_title = f"Total des visites : {VisitCounter.objects.count()}"

@admin.register(VIHProfile)
class VIHProfileAdmin(admin.ModelAdmin):
    # ============================================
    # Sécurité / Permissions
    # ============================================
    VIH_ALLOWED_MODULE_GROUPS = ['VIH Team', 'SMIT', 'Admin VIH']
    VIH_ALLOWED_CHANGE_GROUPS = ['VIH Team', 'Admin VIH']

    def _in_groups(self, request, group_names):
        return request.user.groups.filter(name__in=group_names).exists()

    def has_module_permission(self, request):
        return request.user.is_superuser or self._in_groups(request, self.VIH_ALLOWED_MODULE_GROUPS)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or self._in_groups(request, self.VIH_ALLOWED_CHANGE_GROUPS)

    def has_add_permission(self, request):
        return request.user.is_superuser or self._in_groups(request, self.VIH_ALLOWED_CHANGE_GROUPS)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # ============================================
    # List display
    # ============================================
    list_display = (
        'code_vih_display',
        'patient_link',
        'status_badge',
        'date_diagnostic',
        'date_debut_arv',
        'regimen_code_short',
        'derniere_visite',
        'prochaine_visite_alerte',
        'actions_buttons',
    )
    list_display_links = ('code_vih_display',)
    list_per_page = 25
    ordering = ('-created_at',)

    search_fields = (
        'code_vih',
        'patient__code_patient',
        'patient__nom',
        'patient__prenoms',
        'patient__contact',
        'numero_dossier_vih',
        'regimen_code',
        'provenance',
    )

    # ============================================
    # Filtres (incluant filtres custom)
    # ============================================
    class VisiteRetardFilter(admin.SimpleListFilter):
        title = 'Retard de visite'
        parameter_name = 'visite_retard'

        def lookups(self, request, model_admin):
            return (('oui', 'En retard (> 14 jours)'), ('non', 'À jour'))

        def queryset(self, request, queryset):
            limit = timezone.now().date() - timedelta(days=14)
            if self.value() == 'oui':
                return queryset.filter(status='active', date_derniere_visite__lt=limit)
            if self.value() == 'non':
                return queryset.filter(status='active', date_derniere_visite__gte=limit)
            return queryset

    class StadeOMSFilter(admin.SimpleListFilter):
        title = 'Stade OMS'
        parameter_name = 'oms_stage'

        def lookups(self, request, model_admin):
            return VIHProfile.OMSStage.choices

        def queryset(self, request, queryset):
            if self.value():
                return queryset.filter(oms_stage=self.value())
            return queryset

    list_filter = (
        VisiteRetardFilter,
        StadeOMSFilter,
        'status',
        'vih_type',
        'ligne_traitement',
        'tb_coinfection',
        'hbv_coinfection',
        'hcv_coinfection',
        'adherence_estimee',
        'grossesse_en_cours',
        'allaitement',
        'created_at',
    )

    # ============================================
    # Actions
    # ============================================
    actions = [
        'marquer_actif',
        'marquer_perdu_vue',
        'marquer_transfere',
        'generer_rapport_csv',
        'generer_liste_visites',
    ]

    @admin.action(description="Marquer comme Actif")
    def marquer_actif(self, request, queryset):
        count = queryset.update(status=VIHProfile.VIHStatus.ACTIVE)
        self.message_user(request, f'{count} dossier(s) marqué(s) comme actif(s).', messages.SUCCESS)

    @admin.action(description="Marquer comme Perdu de vue")
    def marquer_perdu_vue(self, request, queryset):
        count = queryset.update(status=VIHProfile.VIHStatus.LOST)
        self.message_user(request, f'{count} dossier(s) marqué(s) comme perdu(s) de vue.', messages.WARNING)

    @admin.action(description="Marquer comme Transféré")
    def marquer_transfere(self, request, queryset):
        count = queryset.update(status=VIHProfile.VIHStatus.TRANSFERRED_OUT)
        self.message_user(request, f'{count} dossier(s) marqué(s) comme transféré(s).', messages.INFO)

    @admin.action(description="Exporter en CSV")
    def generer_rapport_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rapport_vih.csv"'
        writer = csv.writer(response)

        writer.writerow([
            'Code VIH', 'Patient', 'Statut', 'Type VIH', 'Stade OMS',
            'Date diagnostic', 'Date ARV', 'Régimen', 'Ligne traitement',
            'CD4 baseline', 'Dernière visite', 'Prochaine visite',
            'Adhérence', 'Co-infection TB', 'Co-infection HBV', 'Co-infection HCV',
        ])

        for profil in queryset.select_related('patient'):
            writer.writerow([
                profil.code_vih,
                f"{profil.patient.nom} {profil.patient.prenoms}",
                profil.get_status_display(),
                profil.get_vih_type_display(),
                profil.get_oms_stage_display() if profil.oms_stage else '',
                profil.date_diagnostic or '',
                profil.date_debut_arv or '',
                profil.regimen_code or '',
                profil.get_ligne_traitement_display(),
                profil.cd4_baseline or '',
                profil.date_derniere_visite or '',
                profil.date_prochaine_visite or '',
                profil.get_adherence_estimee_display(),
                profil.get_tb_coinfection_display(),
                profil.get_hbv_coinfection_display(),
                profil.get_hcv_coinfection_display(),
            ])
        return response

    @admin.action(description="Générer liste visites (14 jours)")
    def generer_liste_visites(self, request, queryset):
        date_limite = timezone.now().date() + timedelta(days=14)
        qs = queryset.filter(
            status=VIHProfile.VIHStatus.ACTIVE,
            date_prochaine_visite__isnull=False,
            date_prochaine_visite__lte=date_limite
        ).select_related('patient').order_by('date_prochaine_visite')

        response = HttpResponse(content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="visites_prochaines.txt"'

        lines = ["=== LISTE DES VISITES À VENIR (14 prochains jours) ===\n"]
        for profil in qs:
            lines.append(
                f"{profil.code_vih} - {profil.patient.nom} {profil.patient.prenoms} "
                f"({profil.patient.contact}) - Visite: {profil.date_prochaine_visite:%d/%m/%Y}"
            )

        response.write("\n".join(lines))
        return response

    # ============================================
    # Affichage custom (robuste admin)
    # ============================================
    def code_vih_display(self, obj):
        color = {
            'active': '#16a34a',
            'lost': '#dc2626',
            'transferred_out': '#f59e0b',
            'transferred_in': '#2563eb',
            'deceased': '#111827',
            'closed': '#6b7280',
        }.get(obj.status, '#6b7280')
        return format_html('<span style="color:{}; font-weight:800;">{}</span>', color, obj.code_vih)
    code_vih_display.short_description = "Code VIH"
    code_vih_display.admin_order_field = 'code_vih'

    def patient_link(self, obj):
        # URL admin vers le Patient (dynamique, évite les mauvais app_label/model_name)
        patient_app = obj.patient._meta.app_label
        patient_model = obj.patient._meta.model_name
        url = reverse(f'admin:{patient_app}_{patient_model}_change', args=[obj.patient.pk])
        return format_html('<a href="{}" target="_blank">{}</a>', url, f"{obj.patient.nom} {obj.patient.prenoms}")
    patient_link.short_description = "Patient"
    patient_link.admin_order_field = 'patient__nom'

    def status_badge(self, obj):
        styles = {
            'active': ('#16a34a', '#dcfce7'),
            'lost': ('#dc2626', '#fee2e2'),
            'transferred_out': ('#b45309', '#ffedd5'),
            'transferred_in': ('#1d4ed8', '#dbeafe'),
            'deceased': ('#111827', '#e5e7eb'),
            'closed': ('#374151', '#f3f4f6'),
        }
        fg, bg = styles.get(obj.status, ('#374151', '#f3f4f6'))
        return format_html(
            '<span style="display:inline-block;padding:3px 8px;border-radius:999px;'
            'background:{};color:{};font-weight:700;font-size:12px;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = "Statut"
    status_badge.admin_order_field = 'status'

    def regimen_code_short(self, obj):
        if not obj.regimen_code:
            return "—"
        return obj.regimen_code[:30] + "…" if len(obj.regimen_code) > 30 else obj.regimen_code
    regimen_code_short.short_description = "Régimen ARV"

    def derniere_visite(self, obj):
        if not obj.date_derniere_visite:
            return format_html('<span style="color:#6b7280;">Jamais</span>')

        jours = (timezone.now().date() - obj.date_derniere_visite).days
        if jours <= 30:
            color = '#16a34a'
        elif jours <= 90:
            color = '#f59e0b'
        else:
            color = '#dc2626'

        return format_html(
            '<span style="color:{};" title="{} jours">{} ({}j)</span>',
            color, jours, obj.date_derniere_visite.strftime('%d/%m/%Y'), jours
        )
    derniere_visite.short_description = "Dernière visite"
    derniere_visite.admin_order_field = 'date_derniere_visite'

    def prochaine_visite_alerte(self, obj):
        if not obj.date_prochaine_visite:
            return format_html('<span style="color:#6b7280;">Non planifiée</span>')

        jours = (obj.date_prochaine_visite - timezone.now().date()).days
        if jours <= 7:
            fg, bg = '#dc2626', '#fee2e2'
        elif jours <= 14:
            fg, bg = '#b45309', '#ffedd5'
        else:
            fg, bg = '#16a34a', '#dcfce7'

        return format_html(
            '<span style="display:inline-block;padding:3px 8px;border-radius:999px;'
            'background:{};color:{};font-weight:800;font-size:12px;">{}</span>',
            bg, fg, obj.date_prochaine_visite.strftime('%d/%m/%Y')
        )
    prochaine_visite_alerte.short_description = "Prochaine visite"
    prochaine_visite_alerte.admin_order_field = 'date_prochaine_visite'

    def actions_buttons(self, obj):
        # liens admin (robustes)
        app = obj._meta.app_label
        model = obj._meta.model_name

        url_update = reverse(f'admin:{app}_{model}_update_visit', args=[obj.pk])
        url_change = reverse(f'admin:{app}_{model}_change', args=[obj.pk])

        patient_app = obj.patient._meta.app_label
        patient_model = obj.patient._meta.model_name
        url_patient = reverse(f'admin:{patient_app}_{patient_model}_change', args=[obj.patient.pk])

        return format_html(
            '<a class="button" href="{}" title="Mettre à jour la visite">📅</a> '
            '<a class="button" href="{}" title="Voir le détail">👁️</a> '
            '<a class="button" href="{}" target="_blank" title="Dossier patient">🧑‍⚕️</a>',
            url_update, url_change, url_patient
        )
    actions_buttons.short_description = "Actions"

    # ============================================
    # Fieldsets / readonly
    # ============================================
    fieldsets = (
        ('Identification', {
            'fields': ('code_vih', 'patient', 'site_code', 'numero_dossier_vih', 'status'),
            'classes': ('wide',),
        }),
        ('Dates clés', {
            'fields': (
                ('date_diagnostic', 'date_enrolement'),
                ('date_debut_arv', 'date_bilan_baseline'),
                ('date_derniere_visite', 'date_prochaine_visite'),
            ),
            'classes': ('wide',),
        }),
        ('Informations cliniques', {
            'fields': (
                'vih_type',
                'oms_stage',
                ('cd4_baseline', 'charge_virale_baseline'),
                ('tb_coinfection', 'hbv_coinfection', 'hcv_coinfection'),
            ),
            'classes': ('wide',),
        }),
        ('Traitement ARV', {
            'fields': ('regimen_code', 'ligne_traitement', 'adherence_estimee'),
        }),
        ('Contexte spécifique', {
            'fields': (('grossesse_en_cours', 'allaitement'), ('provenance', 'motif_transfert')),
            'classes': ('collapse',),
        }),
        ('Notes et métadonnées', {
            'fields': (
                'notes',
                'extra',
                ('created_by', 'created_at'),
                ('updated_by', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('created_by', 'created_at', 'updated_by', 'updated_at')

    add_fieldsets = (
        ('Patient', {
            'fields': ('patient',),
            'description': 'Sélectionnez le patient pour lequel créer un dossier VIH',
        }),
        ('Informations de base', {
            'fields': ('code_vih', 'date_diagnostic', 'vih_type', 'status'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    # ============================================
    # Form filtering (patient sans dossier)
    # ============================================
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "patient":
            # En ajout uniquement : limiter aux patients sans vih_profile
            # (on détecte l'ajout via l'URL admin)
            is_add = request.path.endswith('/add/')
            if is_add:
                kwargs["queryset"] = Patient.objects.filter(vih_profile__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # notes peut ne pas exister selon ton modèle / exclusions
        if 'notes' in form.base_fields:
            form.base_fields['notes'].widget.attrs.setdefault('rows', 3)
            form.base_fields['notes'].widget.attrs.setdefault('placeholder', 'Notes cliniques importantes...')

        if obj is None and 'date_diagnostic' in form.base_fields:
            form.base_fields['date_diagnostic'].required = True

        return form

    # ============================================
    # Save tracking
    # ============================================
    def save_model(self, request, obj, form, change):
        employee = getattr(request.user, 'employee', None)

        if not change:
            obj.created_by = employee
        obj.updated_by = employee

        # Optionnel (je te conseille de NE PAS recopier code_vih dans Patient pour la discrétion)
        # Mais si tu veux absolument :
        # if not change and not obj.patient.code_vih:
        #     obj.patient.code_vih = obj.code_vih
        #     obj.patient.save(update_fields=['code_vih'])

        super().save_model(request, obj, form, change)

    # ============================================
    # URLs personnalisées
    # ============================================
    def get_urls(self):
        urls = super().get_urls()
        app = self.model._meta.app_label
        model = self.model._meta.model_name

        custom_urls = [
            path(
                '<int:pk>/update_visit/',
                self.admin_site.admin_view(self.update_visit_view),
                name=f'{app}_{model}_update_visit',
            ),
            path(
                'statistics/',
                self.admin_site.admin_view(self.statistics_view),
                name=f'{app}_{model}_statistics',
            ),
        ]
        return custom_urls + urls

    def update_visit_view(self, request, pk):
        if not self.has_change_permission(request):
            raise PermissionDenied

        profil = get_object_or_404(VIHProfile, pk=pk)

        if request.method == 'POST':
            raw = request.POST.get('date_visite')
            if raw:
                try:
                    cleaned = forms.DateField().clean(raw)
                    profil.date_derniere_visite = cleaned
                    profil.save(update_fields=['date_derniere_visite', 'updated_at'])
                    messages.success(request, f'Visite mise à jour pour {profil.code_vih}')
                except forms.ValidationError:
                    messages.error(request, "Date invalide. Format attendu : YYYY-MM-DD.")
            return redirect(f'admin:{profil._meta.app_label}_{profil._meta.model_name}_changelist')

        context = {
            'title': f'Mettre à jour la visite - {profil.code_vih}',
            'profil': profil,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/patients/vihprofile/update_visit.html', context)

    def statistics_view(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied

        total = VIHProfile.objects.count()
        actifs = VIHProfile.objects.filter(status='active').count()
        perdus = VIHProfile.objects.filter(status='lost').count()
        transferes = VIHProfile.objects.filter(status__in=['transferred_out', 'transferred_in']).count()

        visite_7jours = VIHProfile.objects.filter(
            status='active',
            date_prochaine_visite__isnull=False,
            date_prochaine_visite__lte=date.today() + timedelta(days=7)
        ).count()

        oms_stats = VIHProfile.objects.values('oms_stage').annotate(count=Count('oms_stage')).order_by('oms_stage')
        tb_stats = VIHProfile.objects.values('tb_coinfection').annotate(count=Count('tb_coinfection')).order_by('tb_coinfection')

        context = {
            'title': 'Statistiques VIH',
            'total': total,
            'actifs': actifs,
            'perdus': perdus,
            'transferes': transferes,
            'visite_7jours': visite_7jours,
            'oms_stats': oms_stats,
            'tb_stats': tb_stats,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return TemplateResponse(request, 'admin/patients/vihprofile/statistics.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        stats = VIHProfile.objects.values('status').annotate(count=Count('status')).order_by('status')
        retard = VIHProfile.objects.filter(
            status='active',
            date_derniere_visite__isnull=False,
            date_derniere_visite__lt=timezone.now().date() - timedelta(days=14)
        ).count()

        extra_context.update({
            'stats': stats,
            'retard': retard,
            'total': VIHProfile.objects.count(),
        })
        return super().changelist_view(request, extra_context=extra_context)