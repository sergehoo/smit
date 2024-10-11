from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from pharmacy.models import Medicament, CathegorieMolecule, Molecule, MouvementStock, StockAlert, Commande, \
    ArticleCommande, RendezVous


# Create your views here.
class PharmacyListView(LoginRequiredMixin, ListView):
    model = Medicament
    template_name = "pages/pharmacy/medicament_list.html"
    context_object_name = "medicament"
    paginate_by = 50
    ordering = ['-date_expiration']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medicaments = Medicament.objects.all().count()
        context['medicaments_nbr'] = medicaments

        return context


# ListView for displaying all categories
class CathegorieMoleculeListView(ListView):
    model = CathegorieMolecule
    template_name = 'pharmacy/cathegoriemolecule_list.html'  # update with the correct path


# DetailView for a specific category
class CathegorieMoleculeDetailView(DetailView):
    model = CathegorieMolecule
    template_name = 'pharmacy/cathegoriemolecule_detail.html'  # update with the correct path


# CreateView for creating a new category
class CathegorieMoleculeCreateView(CreateView):
    model = CathegorieMolecule
    fields = ['nom', 'description']
    template_name = 'pharmacy/cathegoriemolecule_form.html'  # update with the correct path
    success_url = reverse_lazy('cathegorie_list')


# UpdateView for updating a category
class CathegorieMoleculeUpdateView(UpdateView):
    model = CathegorieMolecule
    fields = ['nom', 'description']
    template_name = 'pharmacy/cathegoriemolecule_form.html'  # update with the correct path
    success_url = reverse_lazy('cathegorie_list')


# # DeleteView for deleting a category
# class CathegorieMoleculeDeleteView(DeleteView):
#     model = CathegorieMolecule
#     template_name = 'pharmacy/cathegoriemolecule_confirm_delete.html'  # update with the correct path
#     success_url = reverse_lazy('cathegorie_list')
#
#
# class MoleculeListView(ListView):
#     model = Molecule
#     template_name = 'pharmacy/molecule_list.html'
#
#
# class MoleculeDetailView(DetailView):
#     model = Molecule
#     template_name = 'pharmacy/molecule_detail.html'
#
#
# class MoleculeCreateView(CreateView):
#     model = Molecule
#     fields = ['nom', 'description', 'cathegorie']
#     template_name = 'pharmacy/molecule_form.html'
#     success_url = reverse_lazy('molecule_list')
#
#
# class MoleculeUpdateView(UpdateView):
#     model = Molecule
#     fields = ['nom', 'description', 'cathegorie']
#     template_name = 'pharmacy/molecule_form.html'
#     success_url = reverse_lazy('molecule_list')
#
#
# class MoleculeDeleteView(DeleteView):
#     model = Molecule
#     template_name = 'pharmacy/molecule_confirm_delete.html'
#     success_url = reverse_lazy('molecule_list')


class MedicamentListView(ListView):
    model = Medicament
    template_name = 'pharmacy/medicament_list.html'


class MedicamentDetailView(DetailView):
    model = Medicament
    template_name = 'pharmacy/medicament_detail.html'


class MedicamentCreateView(CreateView):
    model = Medicament
    fields = ['nom', 'description', 'stock', 'date_expiration', 'categorie', 'fournisseur']
    template_name = 'pharmacy/medicament_form.html'
    success_url = reverse_lazy('medicament_list')


class MedicamentUpdateView(UpdateView):
    model = Medicament
    fields = ['nom', 'description', 'stock', 'date_expiration', 'categorie', 'fournisseur']
    template_name = 'pharmacy/medicament_form.html'
    success_url = reverse_lazy('medicament_list')


class MedicamentDeleteView(DeleteView):
    model = Medicament
    template_name = 'pharmacy/medicament_confirm_delete.html'
    success_url = reverse_lazy('medicament_list')


class MouvementStockListView(ListView):
    model = MouvementStock
    template_name = 'pharmacy/mouvementstock_list.html'


class MouvementStockDetailView(DetailView):
    model = MouvementStock
    template_name = 'pharmacy/mouvementstock_detail.html'


class MouvementStockCreateView(CreateView):
    model = MouvementStock
    fields = ['medicament', 'quantite', 'type_mouvement']
    template_name = 'pharmacy/mouvementstock_form.html'
    success_url = reverse_lazy('mouvementstock_list')


class MouvementStockUpdateView(UpdateView):
    model = MouvementStock
    fields = ['medicament', 'quantite', 'type_mouvement']
    template_name = 'pharmacy/mouvementstock_form.html'
    success_url = reverse_lazy('mouvementstock_list')


class MouvementStockDeleteView(DeleteView):
    model = MouvementStock
    template_name = 'pharmacy/mouvementstock_confirm_delete.html'
    success_url = reverse_lazy('mouvementstock_list')


class StockAlertListView(ListView):
    model = StockAlert
    template_name = 'pharmacy/stockalert_list.html'


class StockAlertDetailView(DetailView):
    model = StockAlert
    template_name = 'pharmacy/stockalert_detail.html'


class StockAlertCreateView(CreateView):
    model = StockAlert
    fields = ['medication', 'niveau_critique', 'quantité_actuelle', 'alerté']
    template_name = 'pharmacy/stockalert_form.html'
    success_url = reverse_lazy('stockalert_list')


class StockAlertUpdateView(UpdateView):
    model = StockAlert
    fields = ['medication', 'niveau_critique', 'quantité_actuelle', 'alerté']
    template_name = 'pharmacy/stockalert_form.html'
    success_url = reverse_lazy('stockalert_list')


class StockAlertDeleteView(DeleteView):
    model = StockAlert
    template_name = 'pharmacy/stockalert_confirm_delete.html'
    success_url = reverse_lazy('stockalert_list')


class CommandeListView(ListView):
    model = Commande
    template_name = 'pharmacy/commande_list.html'


class CommandeDetailView(DetailView):
    model = Commande
    template_name = 'pharmacy/commande_detail.html'


class CommandeCreateView(CreateView):
    model = Commande
    fields = ['medicament', 'quantite_commandee', 'date_commande', 'fournisseur', 'statut']
    template_name = 'pharmacy/commande_form.html'
    success_url = reverse_lazy('commande_list')


class CommandeUpdateView(UpdateView):
    model = Commande
    fields = ['medicament', 'quantite_commandee', 'date_commande', 'fournisseur', 'statut']
    template_name = 'pharmacy/commande_form.html'
    success_url = reverse_lazy('commande_list')


class CommandeDeleteView(DeleteView):
    model = Commande
    template_name = 'pharmacy/commande_confirm_delete.html'
    success_url = reverse_lazy('commande_list')


class ArticleCommandeListView(ListView):
    model = ArticleCommande
    template_name = 'pharmacy/articlecommande_list.html'


class ArticleCommandeDetailView(DetailView):
    model = ArticleCommande
    template_name = 'pharmacy/articlecommande_detail.html'


class ArticleCommandeCreateView(CreateView):
    model = ArticleCommande
    fields = ['commande', 'medicament', 'quantite']
    template_name = 'pharmacy/articlecommande_form.html'
    success_url = reverse_lazy('articlecommande_list')


class ArticleCommandeUpdateView(UpdateView):
    model = ArticleCommande
    fields = ['commande', 'medicament', 'quantite']
    template_name = 'pharmacy/articlecommande_form.html'
    success_url = reverse_lazy('articlecommande_list')


class ArticleCommandeDeleteView(DeleteView):
    model = ArticleCommande
    template_name = 'pharmacy/articlecommande_confirm_delete.html'
    success_url = reverse_lazy('articlecommande_list')


class RendezVousListView(ListView):
    model = RendezVous
    template_name = 'pharmacy/rendezvous_list.html'
    context_object_name = 'rendezvous'


class RendezVousDetailView(DetailView):
    model = RendezVous
    template_name = 'pharmacy/rendezvous_detail.html'


class RendezVousCreateView(CreateView):
    model = RendezVous
    fields = ['patient', 'service', 'doctor', 'calendar', 'event', 'date', 'time', 'reason', 'status', 'created_by']
    template_name = 'pharmacy/rendezvous_form.html'
    success_url = reverse_lazy('rendezvous_list')


class RendezVousUpdateView(UpdateView):
    model = RendezVous
    fields = ['patient', 'service', 'doctor', 'calendar']
