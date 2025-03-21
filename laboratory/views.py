import json
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, RequestConfig, LazyPaginator, SingleTableView

from core.ressources import BilanParacliniqueResource
from core.tables import BilanParacliniqueTable
from smit.filters import ExamenDoneFilter
from smit.forms import EchantillonForm, BilanParacliniqueResultForm
from smit.models import Examen, Analyse, Consultation, Echantillon, BilanParaclinique


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


class ExamenListView(ListView):
    model = BilanParaclinique
    template_name = 'lab/examen_list.html'  # Nom du template à créer
    context_object_name = 'examens'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 📌 Récupérer les examens et les organiser par type de bilan
        examens_par_type = defaultdict(list)
        examens = BilanParaclinique.objects.select_related('examen__type_examen', 'patient', 'doctor').filter(
            result__isnull=True  # ✅ Seuls les examens sans résultats
        ).order_by("created_at")

        for examen in examens:

            type_bilan = examen.examen.type_examen.nom if examen.examen.type_examen else "Autres"
            examens_par_type[type_bilan].append({
                "examen": examen,
                "form": BilanParacliniqueResultForm(instance=examen)  # ✅ Associer un formulaire
            })

        # 📌 Passer les données à la vue
        context["examens_by_type"] = dict(examens_par_type)
        context["examens_by_type_json"] = json.dumps({k: len(v) for k, v in examens_par_type.items()})

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


class ExamenDoneListView(SingleTableView, FilterView):
    model = BilanParaclinique
    table_class = BilanParacliniqueTable
    template_name = 'lab/examen_done_list.html'
    paginate_by = 10
    paginator_class = LazyPaginator
    filterset_class = ExamenDoneFilter
    SingleTableView.table_pagination = False

    def get_queryset(self):
        return BilanParaclinique.objects.filter(
            result__isnull=False
        ).select_related('patient', 'doctor', 'examen', 'examen__type_examen')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        RequestConfig(self.request, paginate={"per_page": self.paginate_by}).configure(table)
        # 🛠️ Force le path correct
        table.paginate_url = self.request.resolver_match and self.request.resolver_match.view_name
        return table
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Compter les examens groupés par type
        bilan_counts = (
            BilanParaclinique.objects
            .filter(result__isnull=False)
            .values('examen__type_examen__nom')
            .annotate(count=Count('id'))
            .order_by('examen__type_examen__nom')
        )

        context["type_bilans_counts"] = bilan_counts
        return context


class ExamenResultatsListView(ListView):
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


class ExamenUpdateView(UpdateView):
    model = Examen
    template_name = 'examen_form.html'  # Nom du template à créer
    fields = '__all__'
    success_url = reverse_lazy('examen_list')  # Redirige vers la liste des examens après mise à jour


class ExamenDeleteView(DeleteView):
    model = Examen
    template_name = 'examen_confirm_delete.html'  # Nom du template à créer
    success_url = reverse_lazy('examen_list')  # Redirige vers la liste des examens après suppression


class AnalyseListView(ListView):
    model = Analyse
    template_name = 'analyse_list.html'  # Nom du template à créer
    context_object_name = 'analyses'


class AnalyseDetailView(DetailView):
    model = Analyse
    template_name = 'analyse_detail.html'  # Nom du template à créer
    context_object_name = 'analyse'


class AnalyseCreateView(CreateView):
    model = Analyse
    template_name = 'analyse_form.html'  # Nom du template à créer
    fields = '__all__'  # Utilisez tous les champs du modèle
    success_url = reverse_lazy('analyse_list')  # Redirige vers la liste des analyses après création


class AnalyseUpdateView(UpdateView):
    model = Analyse
    template_name = 'analyse_form.html'  # Nom du template à créer
    fields = '__all__'
    success_url = reverse_lazy('analyse_list')  # Redirige vers la liste des analyses après mise à jour


class AnalyseDeleteView(DeleteView):
    model = Analyse
    template_name = 'analyse_confirm_delete.html'  # Nom du template à créer
    success_url = reverse_lazy('analyse_list')  # Redirige vers la liste des analyses après suppression


class EchantillonListView(ListView):
    model = Echantillon
    template_name = 'echantillon_list.html'  # Nom du template à créer
    context_object_name = 'echantillon'
