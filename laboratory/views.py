import json
import random
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, RequestConfig, LazyPaginator, SingleTableView

from core.models import Patient
from core.ressources import BilanParacliniqueResource
from core.tables import BilanParacliniqueTable
from smit.filters import ExamenDoneFilter, ExamenFilter
from smit.forms import EchantillonForm, BilanParacliniqueResultForm, ResultatAnalyseForm, ResultatValidationForm
from smit.models import Examen, Analyse, Consultation, Echantillon, BilanParaclinique, ExamenStandard, ResultatAnalyse


# Create your views here.
def create_echantillon(request, consultation_id):
    # Récupération de l'examen associé à l'échantillon
    # examen = get_object_or_404(Examen, id=echantillon_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    if request.method == 'POST':
        form = EchantillonForm(request.POST)
        if form.is_valid():
            echantillon = form.save(commit=False)
            # echantillon.analysedemande = examen  # Associe l'examen à l'échantillon
            echantillon.patient = consultation.patient  # Associe l'examen à l'échantillon
            echantillon.consultation = consultation  # Associe l'examen à l'échantillon
            echantillon.save()
            messages.success(request, 'Échantillon créé avec succès.')
            return redirect('detail_consultation', pk=consultation.id)  # Redirige vers la page de détail de l'examen
        else:
            messages.error(request, 'Erreur lors de la création de l\'échantillon.')
    else:
        form = EchantillonForm()  # Affiche un formulaire vide pour la création

    return redirect('detail_consultation', pk=consultation.id)


def delete_echantillon(request, echantillon_id, consultation_id):
    # Récupérer l'objet TestRapideVIH avec l'id fourni
    echantillon = get_object_or_404(Echantillon, id=echantillon_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Vérifie que la requête est bien une requête POST (pour éviter les suppressions accidentelles)

    echantillon.delete()
    messages.success(request, 'L\'echantillon a été supprimé avec succès.')
    # Redirection après suppression (à personnaliser selon vos besoins)
    return redirect('detail_consultation', pk=consultation.id)


def create_echantillon_consultation_generale(request, consultation_id):
    # Récupération de l'examen associé à l'échantillon
    # examen = get_object_or_404(Examen, id=echantillon_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    if request.method == 'POST':
        form = EchantillonForm(request.POST)
        if form.is_valid():
            echantillon = form.save(commit=False)
            # echantillon.analysedemande = examen  # Associe l'examen à l'échantillon
            echantillon.patient = consultation.patient  # Associe l'examen à l'échantillon
            echantillon.consultation = consultation  # Associe l'examen à l'échantillon
            echantillon.save()
            messages.success(request, 'Échantillon créé avec succès.')
            return redirect('consultation_detail', pk=consultation.id)  # Redirige vers la page de détail de l'examen
        else:
            messages.error(request, 'Erreur lors de la création de l\'échantillon.')
    else:
        form = EchantillonForm()  # Affiche un formulaire vide pour la création

    return redirect('consultation_detail', pk=consultation.id)


def delete_echantillon_consultation_generale(request, echantillon_id, consultation_id):
    # Récupérer l'objet TestRapideVIH avec l'id fourni
    echantillon = get_object_or_404(Echantillon, id=echantillon_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Vérifie que la requête est bien une requête POST (pour éviter les suppressions accidentelles)

    echantillon.delete()
    messages.success(request, 'L\'echantillon a été supprimé avec succès.')
    # Redirection après suppression (à personnaliser selon vos besoins)
    return redirect('consultation_detail', pk=consultation.id)


# 📌 Vue pour soumettre les résultats dynamiquement via AJAX

@login_required
@require_POST
def update_examen_result(request, examen_id):
    examen = get_object_or_404(BilanParaclinique, id=examen_id)

    result = request.POST.get("result")
    result_date = request.POST.get("result_date")
    comment = request.POST.get("comment")

    if not result:
        return JsonResponse({"success": False, "errors": "Le résultat est requis."}, status=400)

    # ✅ Si result_date n'est pas fourni, on utilise la date actuelle
    if result_date:
        examen.result_date = result_date
    else:
        examen.result_date = timezone.now()

    examen.result = result
    examen.comment = comment
    examen.status = "completed"
    examen.save()

    return JsonResponse({"success": True, "message": "✅ Résultat enregistré avec succès."})


class ExamenListView(LoginRequiredMixin,ListView):
    model = BilanParaclinique
    template_name = 'lab/examen_list.html'
    context_object_name = 'examens'

    def get_queryset(self):
        self.filterset = ExamenFilter(self.request.GET, queryset=BilanParaclinique.objects.select_related(
            'examen__type_examen', 'patient', 'doctor'
        ).filter(result__isnull=True).order_by("created_at"))
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        examens_par_type = defaultdict(list)
        for examen in self.object_list:
            type_bilan = examen.examen.type_examen.nom if examen.examen.type_examen else "Autres"
            examens_par_type[type_bilan].append({
                "examen": examen,
                "form": BilanParacliniqueResultForm(instance=examen)
            })

        context["examens_by_type"] = dict(examens_par_type)
        context["examens_by_type_json"] = json.dumps({k: len(v) for k, v in examens_par_type.items()})
        context["filter"] = self.filterset  # ✅ Ajout du filtre au contexte
        return context


# class ExamenDoneListView(ListView):
#     model = BilanParaclinique
#     template_name = 'lab/examen_done_list.html'  # Nom du template à créer
#     context_object_name = 'examens'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         # 📌 Récupérer les examens et les organiser par type de bilan
#         examens_par_type = defaultdict(list)
#         examens = BilanParaclinique.objects.select_related('examen__type_examen', 'patient', 'doctor').filter(
#             result__isnull=False).order_by(
#             "created_at")
#
#         for examen in examens:
#             type_bilan = examen.examen.type_examen.nom if examen.examen.type_examen else "Autres"
#             examens_par_type[type_bilan].append(examen)
#
#         # 📌 Passer les données à la vue
#         context["examens_by_type"] = dict(examens_par_type)
#         context["examens_by_type_json"] = json.dumps({k: len(v) for k, v in examens_par_type.items()})
#
#         return context

def export_examens_done(request, format):
    dataset_format = format.lower()

    # Appliquer les mêmes filtres que dans la vue principale
    f = ExamenDoneFilter(request.GET, queryset=BilanParaclinique.objects.filter(result__isnull=False))

    resource = BilanParacliniqueResource()
    dataset = resource.export(f.qs)

    if dataset_format == 'csv':
        export_data = dataset.csv
        content_type = 'text/csv'
        filename = 'examens_done.csv'
    elif dataset_format == 'xls':
        export_data = dataset.xls
        content_type = 'application/vnd.ms-excel'
        filename = 'examens_done.xls'
    else:
        return HttpResponse("Format non supporté", status=400)

    response = HttpResponse(export_data, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def examens_by_type_paginated(request, type_slug):
    type_slug = type_slug.lower()
    examens = BilanParaclinique.objects.filter(
        result__isnull=False,
        examen__type_examen__nom__iexact=type_slug
    ).select_related("patient", "doctor", "examen", "examen__type_examen")

    paginator = Paginator(examens, 10)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)

    if request.headers.get("HX-Request"):
        return render(request, "partials/_examens_paginated_list.html", {
            "page_obj": page_obj,
            "type_bilan": type_slug.capitalize()
        })

    return HttpResponse(status=400)


class ExamenDoneListView(LoginRequiredMixin,FilterView, ListView):
    model = BilanParaclinique
    template_name = 'lab/examen_done_list.html'
    context_object_name = 'examens'
    paginate_by = 10
    filterset_class = ExamenDoneFilter

    def get_queryset(self):
        return BilanParaclinique.objects.filter(
            result__isnull=False
        ).select_related('patient', 'doctor', 'examen', 'examen__type_examen')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bilan_counts = (
            BilanParaclinique.objects
            .filter(result__isnull=False)
            .values('examen__type_examen__nom')
            .annotate(count=Count('id'))
            .order_by('examen__type_examen__nom')
        )
        context["type_bilans_counts"] = bilan_counts
        return context


class ExamenResultatsListView(LoginRequiredMixin,ListView):
    model = Examen
    template_name = 'lab/examen_result_list.html'  # Nom du template à créer
    context_object_name = 'resultats'


class ExamenDetailView(DetailView):
    model = Examen
    template_name = 'examen_detail.html'  # Nom du template à créer
    context_object_name = 'examen'


class ExamenCreateView(CreateView):
    model = Examen
    template_name = 'examen_form.html'  # Nom du template à créer
    fields = '__all__'
    success_url = reverse_lazy('examen_list')  # Redirige vers la liste des examens après création


class ExamenUpdateView(LoginRequiredMixin,UpdateView):
    model = Examen
    template_name = 'examen_form.html'  # Nom du template à créer
    fields = '__all__'
    success_url = reverse_lazy('examen_list')  # Redirige vers la liste des examens après mise à jour


class ExamenDeleteView(LoginRequiredMixin,DeleteView):
    model = Examen
    template_name = 'examen_confirm_delete.html'  # Nom du template à créer
    success_url = reverse_lazy('examen_list')  # Redirige vers la liste des examens après suppression


class AnalyseListView(ListView):
    model = Analyse
    template_name = 'analyse_list.html'  # Nom du template à créer
    context_object_name = 'analyses'


class AnalyseDetailView(LoginRequiredMixin,DetailView):
    model = Analyse
    template_name = 'analyse_detail.html'  # Nom du template à créer
    context_object_name = 'analyse'


class AnalyseCreateView(LoginRequiredMixin,CreateView):
    model = Analyse
    template_name = 'analyse_form.html'  # Nom du template à créer
    fields = '__all__'  # Utilisez tous les champs du modèle
    success_url = reverse_lazy('analyse_list')  # Redirige vers la liste des analyses après création


class AnalyseUpdateView(LoginRequiredMixin,UpdateView):
    model = Analyse
    template_name = 'analyse_form.html'  # Nom du template à créer
    fields = '__all__'
    success_url = reverse_lazy('analyse_list')  # Redirige vers la liste des analyses après mise à jour


class AnalyseDeleteView(LoginRequiredMixin,DeleteView):
    model = Analyse
    template_name = 'analyse_confirm_delete.html'  # Nom du template à créer
    success_url = reverse_lazy('analyse_list')  # Redirige vers la liste des analyses après suppression


class EchantillonListView(LoginRequiredMixin,ListView):
    model = Echantillon
    template_name = 'echantillon_list.html'  # Nom du template à créer
    context_object_name = 'echantillon'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Comptes dynamiques
        total_en_attente = Echantillon.objects.filter(status_echantillons='Demande').count()
        total_analyse = Echantillon.objects.filter(status_echantillons='Analysé').count()
        total_rejete = Echantillon.objects.filter(status_echantillons='Rejeté').count()
        total_stock = Echantillon.objects.filter(used=False).count()

        # Tu peux ajouter un pourcentage si tu veux les barres de progression réalistes
        total_all = Echantillon.objects.count() or 1  # éviter division par zéro

        context['total_en_attente'] = total_en_attente
        context['pourcent_en_attente'] = round(total_en_attente / total_all * 100)

        context['total_analyse'] = total_analyse
        context['pourcent_analyse'] = round(total_analyse / total_all * 100)

        context['total_rejete'] = total_rejete
        context['pourcent_rejete'] = round(total_rejete / total_all * 100)

        context['total_stock'] = total_stock
        context['pourcent_stock'] = round(total_stock / total_all * 100)

        return context


@login_required
def request_serologie_vih(request):
    patient_id = request.GET.get('patient')
    consultation_id = request.GET.get('consultation')

    patient = get_object_or_404(Patient, pk=patient_id)
    consultation = get_object_or_404(Consultation, pk=consultation_id)

    # Optionnel : tu peux chercher un `Examen` standardisé pour sérologie VIH
    examen = ExamenStandard.objects.filter(nom__icontains='Sérologie VIH').first()

    Echantillon.objects.create(
        patient=patient,
        consultation=consultation,
        examen_demande=examen,
        status_echantillons='Demande',
        test_rapid=True
    )

    messages.success(request, "✅ Demande de prélèvement sérologie VIH créée.")
    return redirect('consultation_detail', pk=consultation_id)


def generate_echantillon_code():
    """
    Génère un code échantillon à 8 chiffres, commençant par 2.
    Exemple : 23456789
    """
    code = f"2{random.randint(1000000, 9999999)}"
    return code


@login_required
def validate_serologie_vih_request(request, preleve_id):
    # ⚡️ Récupérer l’échantillon existant
    echantillon = get_object_or_404(Echantillon, pk=preleve_id)

    # Vérifier si déjà validé
    if echantillon.status_echantillons == 'Validé':
        messages.info(request, "✅ Cette demande est déjà validée.")
        return redirect('echantillons_list')

    # Compléter les champs si besoin
    echantillon.status_echantillons = 'Validé'

    # S'assurer que l’examen demandé est bien un Examen VIH
    if not echantillon.examen_demande:
        examen_vih = ExamenStandard.objects.filter(
            nom__icontains="VIH"
        ).first()
        if examen_vih:
            echantillon.examen_demande = examen_vih

    # Générer un code si absent
    if not echantillon.code_echantillon:
        echantillon.code_echantillon = f"2{random.randint(1000000, 9999999)}"

    echantillon.save()

    messages.success(request, "✅ Demande de prélèvement validée et mise à jour.")
    return redirect('echantillons_list')


@login_required
def update_echantillon_result(request, pk):
    echantillon = get_object_or_404(Echantillon, pk=pk)

    if request.method == 'POST':
        echantillon.resultat = request.POST.get('resultat')
        date_analyse = request.POST.get('date_analyse')
        if date_analyse:
            echantillon.date_analyse = datetime.strptime(date_analyse, '%Y-%m-%dT%H:%M')
        echantillon.commentaire_resultat = request.POST.get('commentaire', '')
        echantillon.save()

        messages.success(request, 'Le résultat a été mis à jour avec succès.')
        return redirect('echantillon_detail', pk=echantillon.pk)

    return redirect('echantillon_detail', pk=echantillon.pk)


class EchantillonDetailView(LoginRequiredMixin,DetailView):
    model = Echantillon
    template_name = 'laboratoire/echantillon_detail.html'
    context_object_name = 'echantillon'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        echantillon = self.object

        # Historique des modifications
        context['history'] = echantillon.history.all()[:5]

        # Statut du prélèvement
        context['status_info'] = self.get_status_info(echantillon)

        # Informations complémentaires
        context['storage_info'] = {
            'location': echantillon.storage_location or "Non spécifié",
            'temperature': echantillon.storage_temperature or "Non spécifié",
        }

        return context

    def get_status_info(self, echantillon):
        """Retourne les informations de statut formatées"""
        status_map = {
            'En attente': {'class': 'warning', 'icon': 'clock'},
            'Analysé': {'class': 'success', 'icon': 'check-circle'},
            'Rejeté': {'class': 'danger', 'icon': 'times-circle'},
            'Stocké': {'class': 'info', 'icon': 'box'}
        }
        status = echantillon.status_echantillons or 'En attente'
        return {
            'text': status,
            'class': status_map.get(status, {}).get('class', 'secondary'),
            'icon': status_map.get(status, {}).get('icon', 'question-circle')
        }


class EchantillonCreateView(LoginRequiredMixin,CreateView):
    model = Echantillon
    template_name = 'laboratoire/echantillon_form.html'
    fields = [
        'code_echantillon', 'examen_demande', 'type', 'cathegorie',
        'patient', 'consultation', 'suivi', 'date_collect', 'site_collect',
        'agent_collect', 'volume', 'storage_information', 'storage_location',
        'storage_temperature',
        'status_echantillons',  # Assure-toi qu'il est dans ton modèle
        'linked', 'used',  # Très utile pour les tests rapides
        'resultat',  # Si tu l’as ajouté pour VIH antigénique
    ]
    success_url = reverse_lazy('echantillon_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # ✅ Fermer correctement ton Q(...)
        form.fields['patient'].queryset = Patient.objects.filter(
            Q(status='actif') | Q(status='hospitalisé')
        )

        form.fields['date_collect'].widget.attrs.update({'class': 'datetimepicker'})

        form.fields['examen_demande'].queryset = Examen.objects.all()

        return form

    def form_valid(self, form):
        # ✅ Génère un code unique
        form.instance.code_echantillon = self.generate_echantillon_code()

        # ✅ Si ton modèle a bien created_by
        if hasattr(form.instance, 'created_by'):
            form.instance.created_by = self.request.user

        response = super().form_valid(form)
        messages.success(self.request, "✅ Prélèvement créé avec succès !")
        return response

    def generate_echantillon_code(self):
        """Génère un code unique basé sur date/heure"""
        prefix = "ECH"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}{timestamp}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Nouveau Prélèvement"
        context['help_text'] = "Remplissez tous les champs requis pour enregistrer un nouveau prélèvement."
        return context


class ResultatAnalyseListView(LoginRequiredMixin, ListView):
    model = ResultatAnalyse
    template_name = 'laboratory/resultatanalyse_list.html'
    context_object_name = 'resultats'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'echantillon', 'valide_par', 'echantillon__patient'
        ).order_by('-date_resultat')

        # Filtres
        self.status_filter = self.request.GET.get('status')
        self.patient_filter = self.request.GET.get('patient')
        self.date_filter = self.request.GET.get('date_range')

        if self.status_filter:
            queryset = queryset.filter(status=self.status_filter)

        if self.patient_filter:
            queryset = queryset.filter(echantillon__patient__id=self.patient_filter)

        if self.date_filter:
            if self.date_filter == 'today':
                queryset = queryset.filter(date_resultat__date=timezone.now().date())
            elif self.date_filter == 'week':
                queryset = queryset.filter(date_resultat__gte=timezone.now() - timedelta(days=7))
            elif self.date_filter == 'month':
                queryset = queryset.filter(date_resultat__gte=timezone.now() - timedelta(days=30))

        # Restriction pour les techniciens (ne voient que leurs résultats)
        if not self.request.user.has_perm('laboratory.view_all_resultats'):
            queryset = queryset.filter(created_by=self.request.user)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ResultatAnalyse.STATUS_CHOICES
        context['filters'] = {
            'status': self.status_filter,
            'patient': self.patient_filter,
            'date_range': self.date_filter,
        }
        return context


class ResultatAnalyseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ResultatAnalyse
    form_class = ResultatAnalyseForm
    template_name = 'laboratory/resultatanalyse_form.html'
    permission_required = 'laboratory.add_resultatanalyse'
    success_url = reverse_lazy('resultatanalyse_list')

    def get_initial(self):
        initial = super().get_initial()
        if 'echantillon_id' in self.kwargs:
            echantillon = get_object_or_404(Echantillon, pk=self.kwargs['echantillon_id'])
            initial['echantillon'] = echantillon
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Résultat créé avec succès!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Créer un nouveau résultat"
        return context
class ResultatAnalyseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ResultatAnalyse
    form_class = ResultatAnalyseForm
    template_name = 'laboratory/resultatanalyse_form.html'
    permission_required = 'laboratory.change_resultatanalyse'
    success_url = reverse_lazy('resultatanalyse_list')

    def dispatch(self, request, *args, **kwargs):
        # Empêcher la modification des résultats validés sans permission spéciale
        obj = self.get_object()
        if obj.est_valide and not request.user.has_perm('laboratory.can_modify_validated'):
            raise PermissionDenied("Vous ne pouvez pas modifier un résultat validé")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Résultat mis à jour avec succès!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modifier le résultat #{self.object.id}"
        return context


class ResultatAnalyseDetailView(LoginRequiredMixin, DetailView):
    model = ResultatAnalyse
    template_name = 'laboratory/resultatanalyse_detail.html'
    context_object_name = 'resultat'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resultat = self.object

        context['title'] = f"Résultat #{resultat.id}"
        context['can_validate'] = self.request.user.has_perm('laboratory.validate_resultatanalyse')
        context['history'] = resultat.history.all().order_by('-history_date')[:10]

        # Statistiques pour l'échantillon
        context['stats'] = {
            'total_resultats': ResultatAnalyse.objects.filter(
                echantillon=resultat.echantillon
            ).count(),
            'resultats_valides': ResultatAnalyse.objects.filter(
                echantillon=resultat.echantillon,
                status='validated'
            ).count(),
        }

        return context


class ResultatAnalyseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ResultatAnalyse
    template_name = 'laboratory/resultatanalyse_confirm_delete.html'
    permission_required = 'laboratory.delete_resultatanalyse'
    success_url = reverse_lazy('resultatanalyse_list')

    def dispatch(self, request, *args, **kwargs):
        # Empêcher la suppression des résultats validés
        obj = self.get_object()
        if obj.est_valide:
            raise PermissionDenied("Vous ne pouvez pas supprimer un résultat validé")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Résultat supprimé avec succès!")
        return super().delete(request, *args, **kwargs)


class ResultatAnalyseValidateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ResultatAnalyse
    form_class = ResultatValidationForm
    template_name = 'laboratory/resultatanalyse_validate.html'
    permission_required = 'laboratory.validate_resultatanalyse'

    def form_valid(self, form):
        form.instance.valide_par = self.request.user
        form.instance.status = 'validated'
        response = super().form_valid(form)
        messages.success(self.request, "Résultat validé avec succès!")
        return response

    def get_success_url(self):
        return reverse('resultatanalyse_detail', kwargs={'pk': self.object.pk})


class ResultatAnalyseCorrigerView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ResultatAnalyse
    form_class = ResultatAnalyseForm
    template_name = 'laboratory/resultatanalyse_correct.html'
    permission_required = 'laboratory.correct_resultatanalyse'
    success_url = reverse_lazy('resultatanalyse_list')

    def get_initial(self):
        initial = super().get_initial()
        initial['status'] = 'corrected'
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Résultat marqué comme corrigé!")
        return response


# Vue API pour la validation AJAX
def validate_resultat_ajax(request, pk):
    if not request.user.has_perm('laboratory.validate_resultatanalyse'):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    resultat = get_object_or_404(ResultatAnalyse, pk=pk)

    if resultat.marquer_comme_valide(request.user):
        return JsonResponse({
            'success': True,
            'status': resultat.get_status_display(),
            'validated_by': resultat.valide_par.get_full_name(),
            'validated_at': timezone.now().strftime("%d/%m/%Y %H:%M")
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Le résultat est déjà validé'
        })