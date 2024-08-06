from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView

from pharmacy.models import Medicament


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
