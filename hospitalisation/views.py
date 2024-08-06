import uuid
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView

from smit.forms import HospitalizationSendForm
from smit.models import Hospitalization, UniteHospitalisation, Consultation


# Create your views here.
class HospitalisationListView(LoginRequiredMixin, ListView):
    model = Hospitalization
    template_name = "pages/hospitalisation/hospitalisation.html"
    context_object_name = "hospitalisationgenerale"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        demande_hospi = Consultation.objects.filter(hospitalised=1).order_by('created_at')
        demande_hospi_nbr = demande_hospi.count()

        # Récupérer la dernière constante pour chaque patient

        context['demande_hospi'] = demande_hospi
        context['demande_hospi_nbr'] = demande_hospi_nbr
        context['demande_hospi_form'] = HospitalizationSendForm()


        return context


class HospitalisationUniteListView(LoginRequiredMixin, ListView):
    model = UniteHospitalisation
    template_name = "pages/hospitalisation/hospi_unite.html"
    context_object_name = "unites"
