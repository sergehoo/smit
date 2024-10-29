import uuid
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.views.generic import ListView, DetailView
from xhtml2pdf import pisa

from smit.forms import HospitalizationSendForm, ConstanteForm, PrescriptionForm, SigneFonctionnelForm, \
    IndicateurBiologiqueForm, IndicateurFonctionnelForm, IndicateurSubjectifForm, PrescriptionHospiForm, \
    HospitalizationIndicatorsForm
from smit.models import Hospitalization, UniteHospitalisation, Consultation, Constante, Prescription, SigneFonctionnel, \
    IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, HospitalizationIndicators


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


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


# Constante PDF Export View
def export_constante_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    constantes = Constante.objects.filter(hospitalisation=hospitalisation)
    context = {
        'hospitalisation': hospitalisation,
        'constantes': constantes
    }
    pdf = render_to_pdf('pdf_templates/constantes_pdf.html', context)
    return pdf


# Prescription PDF Export View
def export_prescription_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    prescriptions = Prescription.objects.filter(patient=hospitalisation.patient)
    context = {
        'hospitalisation': hospitalisation,
        'prescriptions': prescriptions
    }
    pdf = render_to_pdf('pdf_templates/prescriptions_pdf.html', context)
    return pdf


# Signe Fonctionnel PDF Export View
def export_signe_fonctionnel_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    signes_fonctionnels = SigneFonctionnel.objects.filter(hospitalisation=hospitalisation)
    context = {
        'hospitalisation': hospitalisation,
        'signes_fonctionnels': signes_fonctionnels
    }
    pdf = render_to_pdf('pdf_templates/signes_fonctionnels_pdf.html', context)
    return pdf


# Indicateur Biologique PDF Export View
def export_indicateur_biologique_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    indicateurs_biologiques = IndicateurBiologique.objects.filter(hospitalisation=hospitalisation)
    context = {
        'hospitalisation': hospitalisation,
        'indicateurs_biologiques': indicateurs_biologiques
    }
    pdf = render_to_pdf('pdf_templates/indicateurs_biologiques_pdf.html', context)
    return pdf


# Indicateur Fonctionnel PDF Export View
def export_indicateur_fonctionnel_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    indicateurs_fonctionnels = IndicateurFonctionnel.objects.filter(hospitalisation=hospitalisation)
    context = {
        'hospitalisation': hospitalisation,
        'indicateurs_fonctionnels': indicateurs_fonctionnels
    }
    pdf = render_to_pdf('pdf_templates/indicateurs_fonctionnels_pdf.html', context)
    return pdf


# Indicateur Subjectif PDF Export View
def export_indicateur_subjectif_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    indicateurs_subjectifs = IndicateurSubjectif.objects.filter(hospitalisation=hospitalisation)
    context = {
        'hospitalisation': hospitalisation,
        'indicateurs_subjectifs': indicateurs_subjectifs
    }
    pdf = render_to_pdf('pdf_templates/indicateurs_subjectifs_pdf.html', context)
    return pdf


def update_hospitalisation_discharge(request, hospitalisation_id):
    hospitalization = get_object_or_404(Hospitalization, id=hospitalisation_id)

    if request.method == "POST":
        discharge_date = request.POST.get('discharge_date')
        discharge_reason = request.POST.get('discharge_reason')
        status = request.POST.get('status')

        # Update hospitalisation details
        hospitalization.discharge_date = discharge_date
        hospitalization.discharge_reason = discharge_reason
        hospitalization.status = status
        hospitalization.save()

        messages.success(request, f"Hospitalisation details for {hospitalization.patient.nom} updated successfully!")
        return redirect('hospitalisationdetails', pk=hospitalization.id)

    return redirect('hospitalisationdetails', pk=hospitalization.id)


class HospitalisationDetailView(LoginRequiredMixin, DetailView):
    model = Hospitalization
    template_name = "pages/hospitalisation/hospitalisation_details.html"
    context_object_name = "hospitalisationdetail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hospitalization = self.get_object()
        # Récupérer l'enregistrement des indicateurs pour cette hospitalisation
        indicators = hospitalization.indicateurs_autres.last()
        # Préparer les données pour chaque indicateur de sortie
        if indicators:
            context['discharge_criteria'] = {
                'stable_vitals': 1 if indicators.stable_vitals else 0,
                'pain_controlled': 1 if indicators.pain_controlled else 0,
                'functional_ability': 1 if indicators.functional_ability else 0,
                'mental_stability': 1 if indicators.mental_stability else 0,
                'follow_up_plan': 1 if bool(indicators.follow_up_plan) else 0,  # Vérifie si le plan de suivi existe
            }
        else:
            context['discharge_criteria'] = {}
        # Add forms to context
        context['constante_form'] = ConstanteForm()
        context['prescription_form'] = PrescriptionHospiForm()
        context['signe_fonctionnel_form'] = SigneFonctionnelForm()
        context['indicateur_biologique_form'] = IndicateurBiologiqueForm()
        context['indicateur_fonctionnel_form'] = IndicateurFonctionnelForm()
        context['indicateur_subjectif_form'] = IndicateurSubjectifForm()
        context['autresindicatorsform'] = HospitalizationIndicatorsForm()

        context['constantes'] = Constante.objects.filter(hospitalisation=self.object)
        # Retrieve related 'Constante' data for the current hospitalization
        context['constantescharts'] = Constante.objects.filter(hospitalisation=self.object).order_by('created_at')

        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient)
        context['signe_fonctionnel'] = SigneFonctionnel.objects.filter(hospitalisation=self.object)
        context['indicateur_biologique'] = IndicateurBiologique.objects.filter(hospitalisation=self.object)
        context['indicateur_fonctionnel'] = IndicateurFonctionnel.objects.filter(hospitalisation=self.object)
        context['indicateur_subjectif'] = IndicateurSubjectif.objects.filter(hospitalisation=self.object)
        context['indicators'] = HospitalizationIndicators.objects.filter(hospitalisation=self.object)


        return context

    def post(self, request, *args, **kwargs):
        hospitalisation = self.get_object()
        constante_form = ConstanteForm(request.POST)
        prescription_form = PrescriptionForm(request.POST)
        signe_fonctionnel_form = SigneFonctionnelForm(request.POST)
        indicateur_biologique_form = IndicateurBiologiqueForm(request.POST)
        indicateur_fonctionnel_form = IndicateurFonctionnelForm(request.POST)
        indicateur_subjectif_form = IndicateurSubjectifForm(request.POST)

        if constante_form.is_valid():
            constante = constante_form.save(commit=False)
            constante.hospitalisation = hospitalisation
            constante.patient = hospitalisation.patient
            constante.created_by = request.user.employee
            constante.save()
            messages.success(request, "Constante saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        if prescription_form.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.patient = hospitalisation.patient  # Link patient from hospitalisation
            prescription.save()
            messages.success(request, "Prescription saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        if signe_fonctionnel_form.is_valid():
            signe_fonctionnel = signe_fonctionnel_form.save(commit=False)
            signe_fonctionnel.hospitalisation = hospitalisation
            signe_fonctionnel.save()
            messages.success(request, "Signe Fonctionnel saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        if indicateur_biologique_form.is_valid():
            indicateur_biologique = indicateur_biologique_form.save(commit=False)
            indicateur_biologique.hospitalisation = hospitalisation
            indicateur_biologique.save()
            messages.success(request, "Indicateur Biologique saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        if indicateur_fonctionnel_form.is_valid():
            indicateur_fonctionnel = indicateur_fonctionnel_form.save(commit=False)
            indicateur_fonctionnel.hospitalisation = hospitalisation
            indicateur_fonctionnel.save()
            messages.success(request, "Indicateur Fonctionnel saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        if indicateur_subjectif_form.is_valid():
            indicateur_subjectif = indicateur_subjectif_form.save(commit=False)
            indicateur_subjectif.hospitalisation = hospitalisation
            indicateur_subjectif.save()
            messages.success(request, "Indicateur Subjectif saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        # If none of the forms are valid, render the page with errors
        return self.get(request, *args, **kwargs)


class HospitalisationUniteListView(LoginRequiredMixin, ListView):
    model = UniteHospitalisation
    template_name = "pages/hospitalisation/hospi_unite.html"
    context_object_name = "unites"
