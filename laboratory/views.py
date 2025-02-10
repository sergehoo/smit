from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView


from smit.forms import EchantillonForm
from smit.models import Examen, Analyse, Consultation, Echantillon


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


class ExamenListView(ListView):
    model = Examen
    template_name = 'lab/examen_list.html'  # Nom du template à créer
    context_object_name = 'examens'


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
