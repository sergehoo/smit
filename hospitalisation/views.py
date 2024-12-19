import json
import logging
import uuid
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from xhtml2pdf import pisa

from core.models import Patient, ServiceSubActivity
from smit.forms import HospitalizationSendForm, ConstanteForm, PrescriptionForm, SigneFonctionnelForm, \
    IndicateurBiologiqueForm, IndicateurFonctionnelForm, IndicateurSubjectifForm, PrescriptionHospiForm, \
    HospitalizationIndicatorsForm, HospitalizationreservedForm
from smit.models import Hospitalization, UniteHospitalisation, Consultation, Constante, Prescription, SigneFonctionnel, \
    IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, HospitalizationIndicators, LitHospitalisation, \
    ComplicationsIndicators, PrescriptionExecution


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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
def export_indicateur_subjectif_pdf(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    indicateurs_subjectifs = IndicateurSubjectif.objects.filter(hospitalisation=hospitalisation)
    context = {
        'hospitalisation': hospitalisation,
        'indicateurs_subjectifs': indicateurs_subjectifs
    }
    pdf = render_to_pdf('pdf_templates/indicateurs_subjectifs_pdf.html', context)
    return pdf


@login_required
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


# def nurse_dashboard(request):
#     # Filtrer les prescriptions pour les patients hospitalisés avec statut "Pending"
#     pending_prescriptions = Prescription.objects.filter(
#         status='Pending',
#         hospitalisation__isnull=False
#     ).select_related('patient', 'medication', 'hospitalisation')
#
#     # Exécutions passées
#     executed_prescriptions = PrescriptionExecution.objects.filter(
#         executed_by=request.user
#     ).select_related('prescription')
#
#     context = {
#         'pending_prescriptions': pending_prescriptions,
#         'executed_prescriptions': executed_prescriptions,
#     }
#     return render(request, 'nurse_dashboard.html', context)


# def execute_prescription(request, hospitalisation_id, prescription_id):
#     hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
#     prescription = get_object_or_404(Prescription, id=prescription_id, hospitalisation=hospitalisation)
#
#     if request.method == 'POST':
#         form = PrescriptionExecutionForm(request.POST)
#         if form.is_valid():
#             execution = form.save(commit=False)
#             execution.prescription = prescription
#             execution.executed_by = request.user
#             execution.status = 'Administered'
#             execution.save()
#
#             # Mettre à jour le statut de la prescription
#             prescription.status = 'Administered'
#             prescription.save()
#
#             return redirect('nurse_dashboard')  # Ou une autre vue pertinente
#     else:
#         form = PrescriptionExecutionForm()
#
#     return render(
#         request,
#         'pages/hospitalisation/execute_prescription.html',
#         {'form': form, 'prescription': prescription, 'hospitalisation': hospitalisation}
#     )
def mark_execution_taken(request):
    """
    Vue pour marquer une exécution de prescription comme prise.
    """
    if request.method == "POST":
        execution_id = request.POST.get("execution_id")

        # Vérifier si l'ID est valide
        execution = get_object_or_404(PrescriptionExecution, id=execution_id)

        if execution.status != 'Pending':
            messages.warning(request, "Cette exécution a déjà été marquée comme prise ou manquée.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Marquer l'exécution comme prise
        execution.status = "Taken"
        execution.executed_at = now()
        execution.executed_by = request.user.employee  # Associer l'utilisateur qui a marqué l'exécution
        execution.save()

        messages.success(request, "Exécution marquée comme prise avec succès.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Retour en cas de méthode GET
    messages.error(request, "Action non autorisée.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_prescription(request, prescription_id):
    """
    Vue pour supprimer une prescription.
    """
    if request.method == "POST":
        prescription = get_object_or_404(Prescription, id=prescription_id)
        prescription.delete()
        messages.success(request, "Prescription supprimée avec succès.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        messages.error(request, "Action non autorisée.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
class HospitalisationDetailView(LoginRequiredMixin, DetailView):
    model = Hospitalization
    template_name = "pages/hospitalisation/hospitalisation_details.html"
    context_object_name = "hospitalisationdetail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hospitalization = self.get_object()

        # Initialiser labcompliq par défaut
        labcompliq = {"indicators": []}

        complications = hospitalization.indicateurs_compliques.first()  # supposons une seule entrée

        # Si les complications existent, structure les données et les seuils
        if complications:
            indicators = {
                "Sodium": {"value": complications.sodium, "range": ComplicationsIndicators.SODIUM_NORMAL_RANGE},
                "Potassium": {"value": complications.potassium,
                              "range": ComplicationsIndicators.POTASSIUM_NORMAL_RANGE},
                "Chlorure": {"value": complications.chlorure, "range": ComplicationsIndicators.CHLORURE_NORMAL_RANGE},
                "Calcium": {"value": complications.calcium, "range": ComplicationsIndicators.CALCIUM_NORMAL_RANGE},
                "Magnésium": {"value": complications.magnesium,
                              "range": ComplicationsIndicators.MAGNESIUM_NORMAL_RANGE},
                "Phosphate": {"value": complications.phosphate,
                              "range": ComplicationsIndicators.PHOSPHATE_NORMAL_RANGE},
                "Créatinine": {"value": complications.creatinine,
                               "range": ComplicationsIndicators.CREATININE_NORMAL_RANGE_MALE},
                "BUN": {"value": complications.bun, "range": ComplicationsIndicators.BUN_NORMAL_RANGE},
                "ALT": {"value": complications.alt, "range": ComplicationsIndicators.ALT_NORMAL_RANGE},
                "AST": {"value": complications.ast, "range": ComplicationsIndicators.AST_NORMAL_RANGE},
                "Bilirubine Totale": {"value": complications.bilirubine_totale,
                                      "range": ComplicationsIndicators.BILIRUBINE_TOTAL_NORMAL_RANGE},
                "Albumine": {"value": complications.albumine, "range": ComplicationsIndicators.ALBUMINE_NORMAL_RANGE},
                "ALP": {"value": complications.alp, "range": ComplicationsIndicators.ALP_NORMAL_RANGE}
            }

            # Données finales pour le graphique, regroupées par segments
            labcompliq = {
                "indicators": []
            }
            for key, value in indicators.items():
                min_normal = Decimal(value["range"][0])
                max_normal = Decimal(value["range"][1])
                actual = value["value"]

                if actual is None:
                    normal_part = max_normal - min_normal
                    additional_part = Decimal(0)
                    actual_within_range = Decimal(0)
                else:
                    actual = Decimal(actual)
                    if min_normal <= actual <= max_normal:
                        normal_part = actual - min_normal
                        actual_within_range = max_normal - actual
                        additional_part = Decimal(0)
                    elif actual < min_normal:
                        normal_part = Decimal(0)
                        additional_part = min_normal - actual
                        actual_within_range = max_normal - min_normal
                    else:
                        normal_part = max_normal - min_normal
                        additional_part = actual - max_normal
                        actual_within_range = Decimal(0)

                labcompliq["indicators"].append({
                    "name": key,
                    "normal_part": float(normal_part),
                    "within_range": float(actual_within_range),
                    "additional_part": float(additional_part),
                    "actual": float(actual)
                })

        complications_indicators = hospitalization.indicateurs_autres.all().order_by('created_at')

        # Structure des données pour le graphique
        complicbarre = {
            "dates": [indicator.created_at.strftime('%Y-%m-%d') for indicator in complications_indicators],
            "pain_level": [indicator.pain_level for indicator in complications_indicators],
            "mental_state": [indicator.mental_state for indicator in complications_indicators],
            "electrolytes_balance": [indicator.electrolytes_balance for indicator in complications_indicators],
            "renal_function": [indicator.renal_function for indicator in complications_indicators],
            "hepatic_function": [indicator.hepatic_function for indicator in complications_indicators]
        }

        # Récupération des indicateurs de complications

        complications_indicators = hospitalization.indicateurs_autres.all()

        # Compter les occurrences des valeurs pour chaque catégorie
        mental_state_counts = dict(Counter([indicator.mental_state for indicator in complications_indicators]))
        electrolytes_balance_counts = dict(
            Counter([indicator.electrolytes_balance for indicator in complications_indicators]))
        renal_function_counts = dict(Counter([indicator.renal_function for indicator in complications_indicators]))
        hepatic_function_counts = dict(Counter([indicator.hepatic_function for indicator in complications_indicators]))

        # Structurer les données pour les graphiques en camembert
        complic = {
            "mental_state": mental_state_counts,
            "electrolytes_balance": electrolytes_balance_counts,
            "renal_function": renal_function_counts,
            "hepatic_function": hepatic_function_counts
        }

        # Récupération des indicateurs fonctionnels associés à l'hospitalisation

        functional_indicators = hospitalization.indicateurs_fonctionnels.all().order_by('date')

        # Structure des données pour le graphique
        donnees = {
            "dates": [indicator.date.strftime('%Y-%m-%d') for indicator in functional_indicators],
            "mobilite": [indicator.mobilite for indicator in functional_indicators],
            "conscience": [indicator.conscience for indicator in functional_indicators],
            "debit_urinaire": [indicator.debit_urinaire for indicator in functional_indicators],
        }

        # Récupération des indicateurs biologiques associés à l'hospitalisation
        hospitalization = self.get_object()
        indicators = hospitalization.indicateurs_biologiques.all().order_by('date')

        # Structure des données pour le graphique
        data = {
            "dates": [indicator.date.strftime('%Y-%m-%d') for indicator in indicators],
            "globules_blancs": [indicator.globules_blancs for indicator in indicators],
            "hemoglobine": [indicator.hemoglobine for indicator in indicators],
            "plaquettes": [indicator.plaquettes for indicator in indicators],
            "crp": [indicator.crp for indicator in indicators],
            "glucose_sanguin": [indicator.glucose_sanguin for indicator in indicators],
        }

        # Conversion en JSON pour le template

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
        context['prescription_hospi_form'] = PrescriptionHospiForm()
        context['signe_fonctionnel_form'] = SigneFonctionnelForm()
        context['indicateur_biologique_form'] = IndicateurBiologiqueForm()
        context['indicateur_fonctionnel_form'] = IndicateurFonctionnelForm()
        context['indicateur_subjectif_form'] = IndicateurSubjectifForm()
        context['autresindicatorsform'] = HospitalizationIndicatorsForm()

        context['constantes'] = Constante.objects.filter(hospitalisation=self.object)
        # Retrieve related 'Constante' data for the current hospitalization
        context['chart_data'] = json.dumps(data, cls=DjangoJSONEncoder)
        context['functional_chart_data'] = json.dumps(donnees, cls=DjangoJSONEncoder)
        context['complications_chart_data'] = json.dumps(complicbarre, cls=DjangoJSONEncoder)
        context['pie_chart_data'] = json.dumps(complic)
        context['lab_ink'] = json.dumps(labcompliq, cls=DjangoJSONEncoder)
        context['constantescharts'] = Constante.objects.filter(hospitalisation=self.object).order_by('created_at')
        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient)
        context['suivie_prescriptions'] = Prescription.objects.filter(hospitalisation=hospitalization)
        prescriptions = Prescription.objects.filter(hospitalisation=hospitalization)
        executions = PrescriptionExecution.objects.filter(prescription__in=prescriptions).order_by('scheduled_time')
        # context['prescriptions'] = prescriptions
        context['executions'] = executions
        # context['prescription_execution_form'] = PrescriptionExecutionForm()
        context['signe_fonctionnel'] = SigneFonctionnel.objects.filter(hospitalisation=self.object)
        context['indicateur_biologique'] = IndicateurBiologique.objects.filter(hospitalisation=self.object)
        context['indicateur_fonctionnel'] = IndicateurFonctionnel.objects.filter(hospitalisation=self.object)
        context['indicateur_subjectif'] = IndicateurSubjectif.objects.filter(hospitalisation=self.object)
        context['indicators'] = HospitalizationIndicators.objects.filter(hospitalisation=self.object)
        
        # Récupérer toutes les exécutions liées à cette hospitalisation
        executions = PrescriptionExecution.objects.filter(
            prescription__hospitalisation=hospitalization
        ).order_by('scheduled_time')
        # Trouver la prochaine prise
        next_execution = executions.filter(scheduled_time__gte=now(), status='Pending').first()
        # Trouver la dernière prise manquée
        # missed_execution = executions.filter(scheduled_time__lt=now(), status='Pending').order_by('-scheduled_time')
        missed_executions = executions.filter(scheduled_time__lt=now(),status='Pending'
        ).order_by('-scheduled_time')
        context['next_execution'] = next_execution
        context['missed_executions'] = missed_executions
        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")  # Get the form type
        hospitalisation = self.get_object()
        constante_form = ConstanteForm(request.POST)
        prescription_form = PrescriptionHospiForm(request.POST)
        signe_fonctionnel_form = SigneFonctionnelForm(request.POST)
        indicateur_biologique_form = IndicateurBiologiqueForm(request.POST)
        indicateur_fonctionnel_form = IndicateurFonctionnelForm(request.POST)
        indicateur_subjectif_form = IndicateurSubjectifForm(request.POST)
        autresindicatorsform = HospitalizationIndicatorsForm()

        # Check which form was submitted and process accordingly
        if form_type == "constante" and constante_form.is_valid():
            constante = constante_form.save(commit=False)
            constante.hospitalisation = hospitalisation
            constante.patient = hospitalisation.patient
            constante.created_by = request.user.employee
            constante.save()
            messages.success(request, "Constante saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        elif form_type == "prescription" and prescription_form.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.patient = hospitalisation.patient
            prescription.hospitalisation = hospitalisation
            prescription.created_by = request.user.employee
            prescription.status = "Pending"
            prescription.save()
            prescription.generate_executions()
            messages.success(request, "Prescription saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        elif form_type == "signe_fonctionnel" and signe_fonctionnel_form.is_valid():
            signe_fonctionnel = signe_fonctionnel_form.save(commit=False)
            signe_fonctionnel.hospitalisation = hospitalisation
            signe_fonctionnel.save()
            messages.success(request, "Signe Fonctionnel saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        elif form_type == "indicateur_biologique" and indicateur_biologique_form.is_valid():
            indicateur_biologique = indicateur_biologique_form.save(commit=False)
            indicateur_biologique.hospitalisation = hospitalisation
            indicateur_biologique.save()
            messages.success(request, "Indicateur Biologique saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        elif form_type == "indicateur_fonctionnel" and indicateur_fonctionnel_form.is_valid():
            indicateur_fonctionnel = indicateur_fonctionnel_form.save(commit=False)
            indicateur_fonctionnel.hospitalisation = hospitalisation
            indicateur_fonctionnel.save()
            messages.success(request, "Indicateur Fonctionnel saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        elif form_type == "complication" and autresindicatorsform.is_valid():
            complication = autresindicatorsform.save(commit=False)
            complication.hospitalisation = hospitalisation
            complication.save()
            messages.success(request, "Indicateur de complications saved successfully.")
            return redirect(reverse('hospitalisationdetails', args=[hospitalisation.id]))

        # If none of the forms are valid or no form type matches, render the page with errors
        return self.get(request, *args, **kwargs)


@require_POST
def set_cleaning_false(request, lit_id):
    lit = get_object_or_404(LitHospitalisation, id=lit_id)
    lit.is_cleaning = False
    lit.save()
    return JsonResponse({'status': 'success', 'message': 'is_cleaning set to False'})


def reserve_bed(request, bed_id):
    bed = get_object_or_404(LitHospitalisation, id=bed_id)
    bed.reserve(request.user.employee)
    messages.success(request, f'le lit {bed} - a été réservé ')
    return redirect('hospi_unites')  # Redirect to your bed list or detail page


def release_bed(request, bed_id):
    bed = get_object_or_404(LitHospitalisation, id=bed_id)
    bed.release_direct_unoccupied()
    messages.success(request, f'le lit {bed} - a été libéré ')
    return redirect('hospi_unites')


def mark_as_out_of_service(request, bed_id):
    bed = get_object_or_404(LitHospitalisation, id=bed_id)
    bed.mark_as_out_of_service()
    messages.success(request, f'le lit {bed} - est hors usage ')
    return redirect('hospi_unites')


def mark_as_cleaning(request, bed_id):
    bed = get_object_or_404(LitHospitalisation, id=bed_id)
    bed.mark_as_cleaning()
    messages.success(request, f'le lit {bed} - est en nettoyage ')
    return redirect('hospi_unites')


def delete_bed(request, bed_id):
    bed = get_object_or_404(LitHospitalisation, id=bed_id)
    bed.delete_bed()
    messages.success(request, f'le lit {bed} - a été suprimé ')
    return redirect('hospi_unites')


@login_required
def hospitalisation_lit_reserved(request, lit_id):
    lit = get_object_or_404(LitHospitalisation, id=lit_id)

    if request.method == 'POST':
        form = HospitalizationreservedForm(request.POST)
        if form.is_valid():
            hospi = form.save(commit=False)
            patient_id = request.POST['patient']
            hospi.patient = get_object_or_404(Patient, id=patient_id)  # Retrieve the patient object
            hospi.admission_date = date.today()
            hospi.created_by = request.user.employee  # Ensure the user has an associated Employee record

            # Set bed and room based on the selected `lit`
            hospi.bed = lit
            hospi.room = lit.box.chambre

            # Update the bed status and assign the patient
            lit.occuper = True
            lit.occupant = hospi.patient
            lit.save()
            hospi.save()
            messages.success(request, 'Patient transféré en hospitalisation avec succès!')
            return redirect('hospitalisation')
        else:
            messages.error(request, 'Le formulaire est invalide. Veuillez vérifier les informations.')
    else:
        form = HospitalizationreservedForm(initial={'bed': lit})  # Pre-fill the bed

    context = {
        'form': form,
        'bed': lit,
    }
    return render(request, 'pages/hospitalisation/hospitalisation_lit_reserved.html', context)


logger = logging.getLogger(__name__)


class HospitalisationUniteListView(LoginRequiredMixin, ListView):
    model = UniteHospitalisation
    template_name = "pages/hospitalisation/hospi_unite.html"
    context_object_name = "unites"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        lits = []
        for lit in LitHospitalisation.objects.all():
            if lit.is_cleaning:
                bed_session_key = f"cleaning_start_{lit.id}"

                # Initialize the start time if not already set
                if bed_session_key not in self.request.session:
                    self.request.session[bed_session_key] = timezone.now().isoformat()

                cleaning_start_time = timezone.datetime.fromisoformat(self.request.session[bed_session_key])
                end_time = cleaning_start_time + timedelta(minutes=20)

                # Convert end_time to a valid ISO 8601 string
                end_time_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
            else:
                end_time_iso = None

            lits.append({
                'id': lit.id,
                'nom': lit.nom,
                'occuper': lit.occuper,
                'occupant': lit.occupant,
                'is_out_of_service': lit.is_out_of_service,
                'is_cleaning': lit.is_cleaning,
                'end_time': end_time_iso,
            })
            context['lits'] = lits
        return context


class LitDetailView(LoginRequiredMixin, DetailView):
    model = LitHospitalisation
    template_name = "pages/hospitalisation/lit_details.html"
    context_object_name = "litdetail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the current bed
        lit = self.get_object()

        # Get the latest hospitalization related to this bed
        current_hospitalization = Hospitalization.objects.filter(bed=lit, discharge_date__isnull=True).first()

        # Add the hospitalization and patient to the context if available
        if current_hospitalization:
            context['hospitalization'] = current_hospitalization
            context['patient'] = current_hospitalization.patient
        else:
            context['hospitalization'] = None
            context['patient'] = None

        return context
