from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.timezone import now
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from pharmacy.models import Medicament, CathegorieMolecule, Molecule, MouvementStock, StockAlert, Commande, \
    ArticleCommande, RendezVous
from smit.forms import MedicamentForm, RescheduleAppointmentForm, RendezVousForm, ArticleCommandeForm, CommandeForm, \
    ArticleCommandeFormSet, MouvementStockForm


# Create your views here.
class PharmacyListView(LoginRequiredMixin, ListView):
    model = Medicament
    template_name = "pages/pharmacy/medicament_list.html"
    context_object_name = "medicament"
    paginate_by = 10
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
    context_object_name = "medicament"
    paginate_by = 12
    ordering = ['-date_expiration']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = CathegorieMolecule.objects.all()
        molecules = Molecule.objects.all()

        context['categorie_list'] = categories
        context['molecule_list'] = molecules

        return context


class MedicamentDetailView(DetailView):
    model = Medicament
    template_name = 'pharmacy/medicament_detail.html'


class MedicamentCreateView(CreateView):
    model = Medicament
    form_class = MedicamentForm
    template_name = 'pharmacy/medicament_form.html'
    success_url = reverse_lazy('medicaments')


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
    context_object_name = 'mouvements'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'medicament', 'patient', 'fournisseur', 'commande', 'employee', 'pharmacie'
        )

        # Filtres
        self.filters = {
            'type': self.request.GET.get('type'),
            'medicament': self.request.GET.get('medicament'),
            'date_range': self.request.GET.get('date_range'),
            'pharmacie': self.request.GET.get('pharmacie'),
        }

        if self.filters['type']:
            queryset = queryset.filter(type_mouvement=self.filters['type'])

        if self.filters['medicament']:
            queryset = queryset.filter(medicament_id=self.filters['medicament'])

        if self.filters['pharmacie']:
            queryset = queryset.filter(pharmacie_id=self.filters['pharmacie'])

        if self.filters['date_range']:
            if self.filters['date_range'] == 'today':
                today = timezone.now().date()
                queryset = queryset.filter(date_mouvement__date=today)
            elif self.filters['date_range'] == 'week':
                week_ago = timezone.now() - timedelta(days=7)
                queryset = queryset.filter(date_mouvement__gte=week_ago)
            elif self.filters['date_range'] == 'month':
                month_ago = timezone.now() - timedelta(days=30)
                queryset = queryset.filter(date_mouvement__gte=month_ago)
            elif self.filters['date_range'] == 'year':
                year_ago = timezone.now() - timedelta(days=365)
                queryset = queryset.filter(date_mouvement__gte=year_ago)

        return queryset.order_by('-date_mouvement')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiques globales
        total_mouvements = self.get_queryset().count()
        total_sorties = self.get_queryset().filter(type_mouvement='Sortie').aggregate(Sum('quantite'))[
                            'quantite__sum'] or 0
        total_entrees = self.get_queryset().filter(type_mouvement='Entrée').aggregate(Sum('quantite'))[
                            'quantite__sum'] or 0

        # Statistiques temporelles
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)
        year_ago = timezone.now() - timedelta(days=365)

        mouvements_today = self.model.objects.filter(date_mouvement__date=today).count()
        mouvements_week = self.model.objects.filter(date_mouvement__gte=week_ago).count()
        mouvements_month = self.model.objects.filter(date_mouvement__gte=month_ago).count()
        mouvements_year = self.model.objects.filter(date_mouvement__gte=year_ago).count()

        # Top médicaments (sorties)
        top_medicaments_sorties = (
            self.model.objects.filter(type_mouvement='Sortie')
            .values('medicament__nom', 'medicament_id')
            .annotate(total=Sum('quantite'), count=Count('id'))
            .order_by('-total')[:5]
        )

        # Top médicaments (entrées)
        top_medicaments_entrees = (
            self.model.objects.filter(type_mouvement='Entrée')
            .values('medicament__nom', 'medicament_id')
            .annotate(total=Sum('quantite'), count=Count('id'))
            .order_by('-total')[:5]
        )

        # Mouvements récents pour le dashboard
        recent_mouvements = self.model.objects.all().order_by('-date_mouvement')[:5]

        context.update({
            'stats': {
                'total_mouvements': total_mouvements,
                'total_sorties': total_sorties,
                'total_entrees': total_entrees,
                'solde': total_entrees - total_sorties,
                'mouvements_today': mouvements_today,
                'mouvements_week': mouvements_week,
                'mouvements_month': mouvements_month,
                'mouvements_year': mouvements_year,
                'top_medicaments_sorties': top_medicaments_sorties,
                'top_medicaments_entrees': top_medicaments_entrees,
            },
            'filters': self.filters,
            'recent_mouvements': recent_mouvements,
            'today': today,
        })

        return context


class MouvementStockDetailView(LoginRequiredMixin, DetailView):
    model = MouvementStock
    template_name = 'pharmacy/mouvementstock_detail.html'
    context_object_name = 'mouvement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mouvement = self.object

        # Informations complémentaires
        context['title'] = f"Détails du mouvement #{mouvement.id}"
        context['now'] = timezone.now()

        # Historique des modifications du médicament associé
        if mouvement.medicament:
            context['stock_history'] = mouvement.medicament.mouvements.all().order_by('-date_mouvement')[:5]

        # Calcul de la durée depuis la création
        context['time_since_creation'] = context['now'] - mouvement.date_mouvement

        # Statistiques pour ce médicament
        if mouvement.medicament:
            context['stats'] = {
                'total_entrees': mouvement.medicament.mouvements.filter(
                    type_mouvement='Entrée'
                ).aggregate(Sum('quantite'))['quantite__sum'] or 0,
                'total_sorties': mouvement.medicament.mouvements.filter(
                    type_mouvement='Sortie'
                ).aggregate(Sum('quantite'))['quantite__sum'] or 0,
                'mouvements_count': mouvement.medicament.mouvements.count(),
            }

        return context


class MouvementStockCreateView(CreateView):
    model = MouvementStock
    form_class = MouvementStockForm
    template_name = 'pharmacy/mouvementstock_form.html'
    success_url = reverse_lazy('mouvementstock_list')

    def get_form_kwargs(self):
        """Passer la requête au formulaire pour accéder à l'utilisateur courant"""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """Validation personnalisée et traitement avant sauvegarde"""
        try:
            # Vérifier le stock pour les sorties
            mouvement = form.save(commit=False)

            if mouvement.type_mouvement == 'Sortie':
                if mouvement.quantite > mouvement.medicament.stock:
                    form.add_error('quantite', f"Stock insuffisant. Stock disponible: {mouvement.medicament.stock}")
                    return self.form_invalid(form)

                # Mettre à jour le stock immédiatement
                mouvement.medicament.stock -= mouvement.quantite
                mouvement.medicament.save()

            elif mouvement.type_mouvement == 'Entrée':
                mouvement.medicament.stock += mouvement.quantite
                mouvement.medicament.save()

            # Assigner l'employé connecté et la pharmacie
            if self.request.user.is_authenticated:
                if hasattr(self.request.user, 'employee'):
                    mouvement.employee = self.request.user.employee
                    if hasattr(self.request.user.employee, 'pharmacie'):
                        mouvement.pharmacie = self.request.user.employee.pharmacie

            mouvement.save()
            messages.success(self.request, "Mouvement de stock enregistré avec succès!")
            return super().form_valid(form)

        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f"Une erreur est survenue: {str(e)}")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        """Ajout d'informations contextuelles supplémentaires"""
        context = super().get_context_data(**kwargs)
        context['title'] = "Créer un nouveau mouvement de stock"
        context['medicaments'] = Medicament.objects.all().order_by('nom')
        return context


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
    context_object_name = 'commandes'


class CommandeDetailView(DetailView):
    model = Commande
    template_name = 'pharmacy/commande_detail.html'


class CommandeCreateView(CreateView):
    model = Commande
    form_class = CommandeForm
    template_name = 'pharmacy/commande_form.html'
    success_url = reverse_lazy('commandes-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['articles_formset'] = ArticleCommandeFormSet(self.request.POST)
        else:
            context['articles_formset'] = ArticleCommandeFormSet(queryset=ArticleCommande.objects.none())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        articles_formset = context['articles_formset']
        if form.is_valid() and articles_formset.is_valid():
            # Sauvegarder la commande
            self.object = form.save()
            # Sauvegarder les articles et les lier à la commande
            articles = articles_formset.save(commit=False)
            for article in articles:
                article.save()
                self.object.articles.add(article)
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)



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
    form_class = ArticleCommandeForm
    template_name = 'pharmacy/article_commande_form.html'

    def form_valid(self, form):
        # Attache la commande si elle est passée dans l'URL
        commande_id = self.kwargs.get('commande_id')
        if commande_id:
            commande = get_object_or_404(Commande, id=commande_id)
            article = form.save()
            commande.articles.add(article)
        return super().form_valid(form)

    def get_success_url(self):
        commande_id = self.kwargs.get('commande_id')
        return reverse_lazy('commande_detail', kwargs={'pk': commande_id})


class ArticleCommandeUpdateView(UpdateView):
    model = ArticleCommande
    fields = ['commande', 'medicament', 'quantite']
    template_name = 'pharmacy/articlecommande_form.html'
    success_url = reverse_lazy('articlecommande_list')


class ArticleCommandeDeleteView(DeleteView):
    model = ArticleCommande
    template_name = 'pharmacy/articlecommande_confirm_delete.html'
    success_url = reverse_lazy('articlecommande_list')


def is_ajax(request):
    """Utility function to check if the request is an AJAX request."""
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


# Function to mark an appointment as completed
def complete_appointment(request, pk):
    rendezvous = get_object_or_404(RendezVous, pk=pk)

    if rendezvous.status == 'Completed':
        messages.info(request, "Ce rendez-vous est déjà marqué comme terminé.")
        return redirect('rendezvous_list')

    medicaments = rendezvous.medicaments.all()

    if medicaments.exists():
        try:
            with transaction.atomic():
                for medicament in medicaments:
                    if medicament.stock <= 0:
                        raise ValidationError(f"Stock insuffisant pour {medicament.nom}")

                    medicament.stock -= 1
                    medicament.save()

                    MouvementStock.objects.create(
                        medicament=medicament,
                        patient=rendezvous.patient,
                        quantite=1,
                        type_mouvement='Sortie'
                    )

                rendezvous.status = 'Completed'
                rendezvous.save()

                messages.success(request, f"Rendez-vous terminé. Mouvement(s) de stock enregistré(s).")

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('rendezvous_list')
    else:
        messages.warning(request, "Aucun médicament associé à ce rendez-vous.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"status": "success", "message": "Appointment marked as completed and stock updated."})

    return redirect('rendezvous_list')


# Function to reschedule an appointment
def reschedule_appointment(request, pk):
    rendezvous = get_object_or_404(RendezVous, pk=pk)

    if request.method == 'POST':
        form = RescheduleAppointmentForm(request.POST, instance=rendezvous)
        if form.is_valid():
            # Save the rescheduled appointment
            rendezvous = form.save(commit=False)
            rendezvous.status = 'Scheduled'  # Update status to Scheduled after rescheduling
            rendezvous.save()

            messages.success(request, f"Le rendez-vous de {rendezvous.patient} a été reprogrammé.")

            if is_ajax(request):
                return JsonResponse({"status": "success", "message": "Appointment rescheduled and status updated."})

            return redirect('rendezvous_list')  # Redirect to the appointment list view
    else:
        form = RescheduleAppointmentForm(instance=rendezvous)

    return render(request, 'pharmacy/reschedule_appointment.html', {
        'form': form,
        'rendezvous': rendezvous
    })


@login_required
def search_rendezvous(request):
    try:
        query = request.GET.get('query', '').strip()
        pharmacie_id = request.user.employee.pharmacie_id  # Ensure this field exists on your model

        # Fetch rendezvous based on the query and pharmacie
        if query:
            rendezvous_list = RendezVous.objects.filter(
                pharmacie_id=pharmacie_id
            ).filter(
                Q(patient__first_name__icontains=query) |
                Q(patient__last_name__icontains=query) |
                Q(medicaments__nom__icontains=query)
            )
        else:
            # Default to all rendezvous for the pharmacie
            rendezvous_list = RendezVous.objects.filter(pharmacie_id=pharmacie_id)

        # Prepare data for the response
        data = []
        for rdv in rendezvous_list:
            try:
                data.append({
                    'patient': f"{rdv.patient.first_name} {rdv.patient.last_name}",
                    'medicaments': rdv.medicaments.nom if rdv.medicaments else "Non spécifié",
                    'date': rdv.date.strftime('%Y-%m-%d'),
                    'time': rdv.time.strftime('%H:%M'),
                    'status': rdv.get_status_display(),
                    'status_class': 'success' if rdv.status == 'Completed' else 'warning' if rdv.status == 'Scheduled' else 'danger',
                    'actions': f"""
                        <a href='/pharmacy/rendezvous/{rdv.id}/complete/' class='btn btn-success btn-sm'>Recupéré</a>
                        <a href='/pharmacy/rendezvous/{rdv.id}/reschedule/' class='btn btn-warning btn-sm'>Reprogrammer</a>
                    """
                })
            except AttributeError as e:
                print(f"Error while processing rendezvous {rdv.id}: {e}")

        return JsonResponse(data, safe=False)

    except Exception as e:
        print(f"Error in search_rendezvous: {str(e)}")
        return JsonResponse({"error": "An error occurred while processing the search."}, status=500)


class RendezVousListView(ListView):
    model = RendezVous
    template_name = 'pharmacy/rendezvous_list.html'
    context_object_name = 'rendezvous_list'
    paginate_by = 10  # Nombre de rendez-vous par page
    ordering = '-created_at'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rdvnbr = self.object_list.count()
        # Filtrer les rendez-vous pour le mois en cours
        current_date = now()
        current_month = current_date.month
        current_year = current_date.year

        cemois = self.object_list.filter(date__year=current_year, date__month=current_month)

        context['nombre_rdv'] = rdvnbr
        context['rdv_ce_mois'] = cemois.count()

        return context

    def get_queryset(self):
        queryset = super().get_queryset().filter(pharmacie=self.request.user.employee.pharmacie_id)
        # Automatically update missed appointments
        today = timezone.now().date()
        queryset.filter(status='Scheduled', date__lt=today).update(status='Missed')
        # Optional filtering by patient
        patient_id = self.request.GET.get('patient')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        return queryset


class RendezVousDetailView(DetailView):
    model = RendezVous
    template_name = 'pharmacy/rendezvous_detail.html'


class RendezVousCreateView(CreateView):
    model = RendezVous
    form_class = RendezVousForm
    template_name = 'pharmacy/rendezvous_form.html'
    success_url = reverse_lazy('rendezvous_list')

    def form_valid(self, form):
        try:
            # Save the form instance without committing to the database
            rdv = form.save(commit=False)

            # Assign the pharmacie from the logged-in user's employee profile
            rdv.pharmacie = self.request.user.employee.pharmacie  # Correct attribute name
            # rdv.pharmacie = self.request.user.employee.pharmacie  # Correct attribute name
            # rdv.pharmacie = self.request.user.employee.pharmacie  # Correct attribute name
            rdv.created_by = self.request.user.employee  # Correct attribute name

            # Save the RendezVous instance to the database
            rdv.save()

            # Create recurrences if applicable
            rdv.create_recurrences()

            # Display a success message
            messages.success(self.request, "Le rendez-vous a été créé avec succès.")
            return super().form_valid(form)

        except AttributeError:
            # Handle the case where the user does not have an associated employee or pharmacie
            messages.error(self.request, "Votre profil n'est pas associé à une pharmacie.")
            return redirect('rendezvous_create')

        except Exception as e:
            # Catch any other exceptions and display an error message
            messages.error(self.request, f"Erreur lors de la création du rendez-vous : {str(e)}")
            return redirect('rendezvous_create')

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)


class RendezVousUpdateView(UpdateView):
    model = RendezVous
    fields = ['patient', 'service', 'doctor', 'calendar']


class RendezVousDeleteView(DeleteView):
    model = RendezVous
    template_name = 'appointments/rendezvous_confirm_delete.html'
    success_url = reverse_lazy('rendezvous_list')
