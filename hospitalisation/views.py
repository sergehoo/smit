import datetime
import json
import logging
import random
import re
import traceback
import uuid
from collections import Counter, defaultdict, OrderedDict
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now, make_naive, is_aware
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa

from core.models import Patient, ServiceSubActivity, Maladie, Employee
from pharmacy.models import Medicament, Medocsprescrits
from smit.forms import HospitalizationSendForm, ConstanteForm, PrescriptionForm, SigneFonctionnelForm, \
    IndicateurBiologiqueForm, IndicateurFonctionnelForm, IndicateurSubjectifForm, PrescriptionHospiForm, \
    HospitalizationIndicatorsForm, HospitalizationreservedForm, EffetIndesirableForm, HistoriqueMaladieForm, \
    DiagnosticForm, AvisMedicalForm, ObservationForm, CommentaireInfirmierForm, PatientSearchForm, \
    HospitalizationUrgenceForm, AntecedentsHospiForm, GroupedAntecedentsForm, ModeDeVieForm, AppareilForm, \
    ResumeSyndromiqueForm, ProblemePoseForm, BilanParacliniqueMultiForm, ImagerieMedicaleForm
from smit.models import Hospitalization, UniteHospitalisation, Consultation, Constante, Prescription, SigneFonctionnel, \
    IndicateurBiologique, IndicateurFonctionnel, IndicateurSubjectif, HospitalizationIndicators, LitHospitalisation, \
    ComplicationsIndicators, PrescriptionExecution, Observation, HistoriqueMaladie, Diagnostic, AvisMedical, \
    EffetIndesirable, CommentaireInfirmier, TypeAntecedent, AntecedentsMedicaux, ModeDeVieCategorie, ModeDeVie, \
    AppareilType, Appareil, BilanParaclinique, ExamenStandard, TypeBilanParaclinique


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


class ExportHospitalizationView(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        current_date = timezone.now().strftime('%Y-%m-%d')
        filename = f"Exportation donnees hospitalisations_{current_date}.xlsx".replace(' ', '_')

        # Convertir les données en DataFrame Pandas
        data = []
        for hosp in queryset:
            admission_date = hosp.admission_date
            discharge_date = hosp.discharge_date

            # Rendre les datetime naïfs si nécessaire
            if is_aware(admission_date):
                admission_date = make_naive(admission_date)
            if discharge_date and is_aware(discharge_date):
                discharge_date = make_naive(discharge_date)

            data.append({
                'Patient': f"{hosp.patient.nom} {hosp.patient.prenoms}",
                'Admission Date': admission_date,
                'Discharge Date': discharge_date or 'En cours',
                'Diagnostic Final': hosp.diagnostics.filter(
                    type_diagnostic='final').first().maladie.nom if hosp.diagnostics.filter(
                    type_diagnostic='final').exists() else 'Aucun',
                'Status': hosp.patient.status,
            })

        df = pd.DataFrame(data)

        # Exporter en fichier Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        df.to_excel(response, index=False, engine='openpyxl')
        return response

    def get_queryset(self):
        queryset = Hospitalization.objects.select_related('patient').prefetch_related('diagnostics')

        # Appliquer les filtres si des paramètres sont présents
        maladie = self.request.GET.get('maladie')
        status = self.request.GET.get('status')
        nom_patient = self.request.GET.get('nom_patient')

        if maladie:
            queryset = queryset.filter(diagnostics__maladie__id=maladie, diagnostics__type_diagnostic='final')
        if status:
            queryset = queryset.filter(patient__status=status)
        if nom_patient:
            queryset = queryset.filter(
                Q(patient__nom__icontains=nom_patient) | Q(patient__prenoms__icontains=nom_patient))

        return queryset.distinct()


class HospitalisationListView(LoginRequiredMixin, ListView):
    model = Hospitalization
    template_name = "pages/hospitalisation/hospitalisation.html"
    context_object_name = "hospitalisationgenerale"
    paginate_by = 10
    ordering = "-admission_date"

    def get_queryset(self):
        queryset = super().get_queryset() \
            .select_related('patient') \
            .prefetch_related('diagnostics') \
            .filter(discharge_date__isnull=True)  # ➡ Filtrer uniquement les hospitalisations en cours

        # Appliquer les filtres de recherche
        maladie = self.request.GET.get('maladie')
        unite = self.request.GET.get('unite')
        status = self.request.GET.get('status')
        nom_patient = self.request.GET.get('nom_patient')

        if unite:
            queryset = queryset.filter(bed__box__chambre__unite__id=unite)

        if maladie:
            queryset = queryset.filter(diagnostics__maladie__id=maladie,
                                       diagnostics__type_diagnostic='final')  # Utilisation de l'ID pour éviter ambiguïtés
        if status:
            queryset = queryset.filter(patient__status=status)
        if nom_patient:
            queryset = queryset.filter(
                Q(patient__nom__icontains=nom_patient) | Q(patient__prenoms__icontains=nom_patient))

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        demande_hospi = Consultation.objects.filter(hospitalised=1).order_by('created_at')
        demande_hospi_nbr = demande_hospi.count()
        queryset = self.get_queryset()

        nbr_patient = UniteHospitalisation.objects.annotate(
            nb_patients_hospitalises=Count(
                'chambres__boxes__lits__lit_hospy__id',
                filter=Q(chambres__boxes__lits__lit_hospy__discharge_date__isnull=True)
            )
        )

        # Définition des tranches d'âge
        age_ranges = {
            "0-18": (today - datetime.timedelta(days=18 * 365), today),
            "18-30": (today - datetime.timedelta(days=30 * 365), today - datetime.timedelta(days=18 * 365)),
            "30-45": (today - datetime.timedelta(days=45 * 365), today - datetime.timedelta(days=30 * 365)),
            "45-60": (today - datetime.timedelta(days=60 * 365), today - datetime.timedelta(days=45 * 365)),
            "60-plus": (None, today - datetime.timedelta(days=60 * 365)),
        }

        # Compter les patients hospitalisés dans chaque tranche d'âge
        age_counts = {}
        for key, (min_date, max_date) in age_ranges.items():
            query = Hospitalization.objects.filter(discharge_date__isnull=True)

            if min_date and max_date:
                query = query.filter(patient__date_naissance__range=(min_date, max_date))
            elif max_date:
                query = query.filter(patient__date_naissance__lte=max_date)

            age_counts[key] = query.count()

        # Ajouter les données au contexte
        context['age_counts'] = age_counts

        # Récupérer la dernière constante pour chaque patient
        context['search_form'] = PatientSearchForm(self.request.GET or None)
        context['demande_hospi'] = demande_hospi
        context['demande_hospi_nbr'] = demande_hospi_nbr
        context['demande_hospi_form'] = HospitalizationSendForm()
        context['result_count'] = queryset.count()
        context['unites_hospitalisation'] = nbr_patient

        return context


def calculate_patient_age(date_naissance):
    """Retourne l'âge d'un patient à partir de sa date de naissance."""
    if not date_naissance:
        return None
    today = datetime.date.today()
    return (today - date_naissance).days // 365


def export_hospitalized_patients(request, age_group):
    """
    Exporte les patients hospitalisés selon une tranche d'âge définie.
    """
    today = datetime.date.today()

    age_ranges = {
        "0-18": (0, 18),
        "18-30": (18, 30),
        "30-45": (30, 45),
        "45-60": (45, 60),
        "60-plus": (60, 150),  # Supposons un âge maximum de 150 ans
    }

    if age_group not in age_ranges:
        return HttpResponse("Tranche d'âge invalide.", status=400)

    min_age, max_age = age_ranges[age_group]

    # Filtrer les patients en fonction de leur âge
    queryset = Hospitalization.objects.filter(discharge_date__isnull=True).select_related("patient", "doctor")

    # Filtrer en fonction de l'âge
    filtered_patients = [
        hospi for hospi in queryset
        if hospi.patient.date_naissance and min_age <= calculate_patient_age(hospi.patient.date_naissance) < max_age
    ]

    # Vérifier s'il y a des résultats
    if not filtered_patients:
        return HttpResponse("Aucun patient trouvé pour cette tranche d'âge.", status=204)

    # Création du DataFrame
    data = [
        {
            "Nom du Patient": hospi.patient.nom,
            "Prénom": hospi.patient.prenoms,
            "Date de Naissance": hospi.patient.date_naissance,
            "Sexe": hospi.patient.sexe,
            "Âge": calculate_patient_age(hospi.patient.date_naissance),
            "Médecin Responsable": hospi.doctor.nom if hospi.doctor else "N/A",
            "Date d'Admission": hospi.admission_date,
            "Chambre": hospi.room,
            "Lit": hospi.bed.id if hospi.bed else "N/A",
            "Motif d'Admission": hospi.reason_for_admission,
        }
        for hospi in filtered_patients
    ]

    df = pd.DataFrame(data)

    # Création du fichier Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Patients_Hospitalisés_{age_group}.xlsx"'

    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Hospitalisations")

    return response


class HospitalisedPatientListView(LoginRequiredMixin, ListView):
    model = Hospitalization
    template_name = "pages/hospitalisation/hospitalised_patient.html"
    context_object_name = "hospitalisationgenerale"
    paginate_by = 10
    ordering = "-admission_date"

    def get_queryset(self):
        queryset = super().get_queryset() \
            .select_related('patient') \
            .prefetch_related('diagnostics') \
            .filter(discharge_date__isnull=False)  # ➡ Filtrer uniquement les hospitalisations en cours

        # Appliquer les filtres de recherche
        maladie = self.request.GET.get('maladie')
        unite = self.request.GET.get('unite')
        status = self.request.GET.get('status')
        nom_patient = self.request.GET.get('nom_patient')

        if unite:
            queryset = queryset.filter(bed__box__chambre__unite__id=unite)

        if maladie:
            queryset = queryset.filter(diagnostics__maladie__id=maladie,
                                       diagnostics__type_diagnostic='final')  # Utilisation de l'ID pour éviter ambiguïtés
        if status:
            queryset = queryset.filter(patient__status=status)
        if nom_patient:
            queryset = queryset.filter(
                Q(patient__nom__icontains=nom_patient) | Q(patient__prenoms__icontains=nom_patient))

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        demande_hospi = Consultation.objects.filter(hospitalised=1).order_by('created_at')
        demande_hospi_nbr = demande_hospi.count()
        queryset = self.get_queryset()

        nbr_patient = UniteHospitalisation.objects.annotate(
            nb_patients_hospitalises=Count(
                'chambres__boxes__lits__lit_hospy__id',
                filter=Q(chambres__boxes__lits__lit_hospy__discharge_date__isnull=False)
            )
        )

        today = date.today()
        queryset = self.get_queryset()

        # Dictionnaire pour stocker le nombre de patients par tranche d'âge
        age_counts = {
            "0-18": 0,
            "18-30": 0,
            "30-45": 0,
            "45-60": 0,
            "60+": 0
        }

        # Calculer l'âge des patients hospitalisés
        for hosp in queryset:
            age = today.year - hosp.patient.date_naissance.year
            if age <= 18:
                age_counts["0-18"] += 1
            elif 18 < age <= 30:
                age_counts["18-30"] += 1
            elif 30 < age <= 45:
                age_counts["30-45"] += 1
            elif 45 < age <= 60:
                age_counts["45-60"] += 1
            else:
                age_counts["60+"] += 1

        context['age_counts'] = age_counts  # Ajout des données au contexte

        # Récupérer la dernière constante pour chaque patient
        context['search_form'] = PatientSearchForm(self.request.GET or None)
        context['demande_hospi'] = demande_hospi
        context['demande_hospi_nbr'] = demande_hospi_nbr
        context['demande_hospi_form'] = HospitalizationSendForm()
        context['result_count'] = queryset.count()
        context['unites_hospitalisation'] = nbr_patient

        return context


class SuivieSoinsListView(LoginRequiredMixin, ListView):
    model = Hospitalization
    template_name = "pages/hospitalisation/suivie_soins.html"
    context_object_name = "suiviesoins"
    paginate_by = 10
    ordering = "-admission_date"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = Hospitalization.objects.select_related(
            'patient', 'bed__box__chambre__unite'
        ).filter(discharge_date__isnull=True)  # Filtrer uniquement les hospitalisations actives

        # Regrouper les hospitalisations par unité
        grouped_queryset = {}
        for hospitalization in queryset:
            unite = hospitalization.bed.box.chambre.unite
            if unite not in grouped_queryset:
                grouped_queryset[unite] = []
            grouped_queryset[unite].append(hospitalization)

        context['grouped_suiviesoins'] = grouped_queryset
        return context


@login_required
def add_hospi_suivie_comment(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)

    if request.method == 'POST':
        form = CommentaireInfirmierForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.patient = hospitalisation.patient
            commentaire.hospitalisation = hospitalisation
            commentaire.medecin = request.user
            commentaire.save()
            messages.success(request, "Commentaire ajouté avec succès.")
            return redirect('suivie_soins_detail', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout du commentaire. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CommentaireInfirmierForm()
    messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
    return redirect('suivie_soins_detail', pk=hospitalisation_id)


@login_required
def add_observations_suivi(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = ObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.hospitalisation = hospitalisation
            observation.patient = hospitalisation.patient
            # observation.date_enregistrement = timezone.now()  # Utilisation correcte du champ dans le modèle
            observation.medecin = request.user  # Associe l'utilisateur actuel comme médecin
            observation.save()
            messages.success(request, "Observation ajoutée avec succès.")
            return redirect('suivie_soins_detail', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout de l'observation. Veuillez corriger les erreurs.")

    messages.error(request, "Erreur lors de l'ajout de l'observation. Veuillez corriger les erreurs ci-dessous.")
    return redirect('suivie_soins_detail', pk=hospitalisation_id)


class SuivieSoinsDetailView(LoginRequiredMixin, DetailView):
    model = Hospitalization
    template_name = "pages/hospitalisation/suivie_soins_details.html"
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

        context['antecedentshospi'] = AntecedentsHospiForm()
        context['prescription_hospi_form'] = PrescriptionHospiForm()
        context['signe_fonctionnel_form'] = SigneFonctionnelForm()
        context['indicateur_biologique_form'] = IndicateurBiologiqueForm()
        context['indicateur_fonctionnel_form'] = IndicateurFonctionnelForm()
        context['indicateur_subjectif_form'] = IndicateurSubjectifForm()
        context['autresindicatorsform'] = HospitalizationIndicatorsForm()

        context['diagnosticsform'] = DiagnosticForm()
        context['observationform'] = ObservationForm()
        context['avismedicalform'] = AvisMedicalForm()
        context['effetindesirableform'] = EffetIndesirableForm()
        context['historiquemaladieform'] = HistoriqueMaladieForm()
        context['hospicomment'] = CommentaireInfirmierForm()

        context['observations'] = Observation.objects.filter(hospitalisation=self.object).order_by(
            '-date_enregistrement')
        context['observationscount'] = Observation.objects.filter(hospitalisation=self.object).count

        context['historiques_maladie'] = HistoriqueMaladie.objects.filter(hospitalisation=self.object).order_by(
            '-date_enregistrement')

        context['diagnostics'] = Diagnostic.objects.filter(hospitalisation=self.object).order_by('-date_diagnostic')
        context['diagnosticscount'] = Diagnostic.objects.filter(hospitalisation=self.object).count()

        context['avis_medicaux'] = AvisMedical.objects.filter(hospitalisation=self.object).order_by('-date_avis')
        context['avis_medicauxcount'] = AvisMedical.objects.filter(hospitalisation=self.object).count()

        context['effets_indesirables'] = EffetIndesirable.objects.filter(hospitalisation=self.object).order_by(
            '-date_signalement')
        context['effets_indesirablescount'] = EffetIndesirable.objects.filter(hospitalisation=self.object).count()

        context['hopi_comment'] = CommentaireInfirmier.objects.filter(hospitalisation=self.object).order_by(
            '-date_commentaire')
        context['hopi_commentcount'] = CommentaireInfirmier.objects.filter(hospitalisation=self.object).count()

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
        executions = PrescriptionExecution.objects.filter(prescription__in=prescriptions,
                                                          scheduled_time__gte=now()).order_by('scheduled_time')

        # context['prescriptions'] = prescriptions
        context['executions'] = executions
        # context['prescription_execution_form'] = PrescriptionExecutionForm()
        context['signe_fonctionnel'] = SigneFonctionnel.objects.filter(hospitalisation=self.object)
        context['indicateur_biologique'] = IndicateurBiologique.objects.filter(hospitalisation=self.object)
        context['indicateur_fonctionnel'] = IndicateurFonctionnel.objects.filter(hospitalisation=self.object)
        context['indicateur_subjectif'] = IndicateurSubjectif.objects.filter(hospitalisation=self.object)
        context['indicators'] = HospitalizationIndicators.objects.filter(hospitalisation=self.object)

        # Récupérer toutes les exécutions liées à cette hospitalisation
        executions = PrescriptionExecution.objects.filter(prescription__hospitalisation=hospitalization).order_by(
            'scheduled_time')
        # Trouver la prochaine prise
        next_execution = executions.filter(scheduled_time__gte=now(), status='Pending').first()
        # Trouver la dernière prise manquée
        # missed_execution = executions.filter(scheduled_time__lt=now(), status='Pending').order_by('-scheduled_time')
        missed_executions = executions.filter(scheduled_time__lt=now(), status='Missed'
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
            return redirect(reverse('suivie_soins_detail', args=[hospitalisation.id]))

        elif form_type == "prescription" and prescription_form.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.patient = hospitalisation.patient
            prescription.hospitalisation = hospitalisation
            prescription.created_by = request.user.employee
            prescription.status = "Pending"
            prescription.save()
            prescription.generate_executions()
            messages.success(request, "Prescription saved successfully.")
            return redirect(reverse('suivie_soins_detail', args=[hospitalisation.id]))

        elif form_type == "signe_fonctionnel" and signe_fonctionnel_form.is_valid():
            signe_fonctionnel = signe_fonctionnel_form.save(commit=False)
            signe_fonctionnel.hospitalisation = hospitalisation
            signe_fonctionnel.save()
            messages.success(request, "Signe Fonctionnel saved successfully.")
            return redirect(reverse('suivie_soins_detail', args=[hospitalisation.id]))

        elif form_type == "indicateur_biologique" and indicateur_biologique_form.is_valid():
            indicateur_biologique = indicateur_biologique_form.save(commit=False)
            indicateur_biologique.hospitalisation = hospitalisation
            indicateur_biologique.save()
            messages.success(request, "Indicateur Biologique saved successfully.")
            return redirect(reverse('suivie_soins_detail', args=[hospitalisation.id]))

        elif form_type == "indicateur_fonctionnel" and indicateur_fonctionnel_form.is_valid():
            indicateur_fonctionnel = indicateur_fonctionnel_form.save(commit=False)
            indicateur_fonctionnel.hospitalisation = hospitalisation
            indicateur_fonctionnel.save()
            messages.success(request, "Indicateur Fonctionnel saved successfully.")
            return redirect(reverse('suivie_soins_detail', args=[hospitalisation.id]))

        elif form_type == "complication" and autresindicatorsform.is_valid():
            complication = autresindicatorsform.save(commit=False)
            complication.hospitalisation = hospitalisation
            complication.save()
            messages.success(request, "Indicateur de complications saved successfully.")
            return redirect(reverse('suivie_soins_detail', args=[hospitalisation.id]))

        # If none of the forms are valid or no form type matches, render the page with errors
        return self.get(request, *args, **kwargs)


class HospitalizationUrgenceCreateView(CreateView):
    model = Hospitalization
    form_class = HospitalizationUrgenceForm
    template_name = "pages/hospitalization/hospitalization_urgence_create.html"
    success_url = reverse_lazy('hospitalisation')  # Redirige après la création


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
def adjust_future_executions(execution):
    """
    Ajuste les exécutions futures en cas de retard dans la prise d'un médicament.
    """
    prescription = execution.prescription
    posology = prescription.posology.strip()

    # 🔄 Mappage des posologies avec leurs intervalles en heures
    POSOLOGY_MAPPING = {
        'Une fois par jour': 24,
        'Deux fois par jour': 12,
        'Trois fois par jour': 8,
        'Quatre fois par jour': 6,
        'Toutes les 4 heures': 4,
        'Toutes les 6 heures': 6,
        'Toutes les 8 heures': 8,
        'Une fois par semaine': 168,  # 7 jours
        'Deux fois par semaine': 84,  # 3,5 jours
        'Un jour sur deux': 48,  # 2 jours
    }

    # Vérifier si la posologie est bien définie
    interval = POSOLOGY_MAPPING.get(posology)
    if interval is None:
        return  # Ne rien faire si la posologie ne suit pas un intervalle fixe

    # 🔍 Récupérer les exécutions futures à ajuster
    future_executions = PrescriptionExecution.objects.filter(
        prescription=prescription,
        scheduled_time__gt=execution.scheduled_time,
        status='Pending'
    ).order_by('scheduled_time')

    # ✅ Ajuster chaque exécution future en fonction du retard
    next_scheduled_time = execution.executed_at + datetime.timedelta(hours=interval)

    with transaction.atomic():
        for future_execution in future_executions:
            future_execution.scheduled_time = next_scheduled_time
            future_execution.save()
            next_scheduled_time += datetime.timedelta(hours=interval)


def mark_execution_taken(request):
    """
    Vue pour marquer une exécution de prescription comme prise et ajuster les exécutions suivantes en cas de retard.
    """
    if request.method == "POST":
        execution_id = request.POST.get("execution_id")

        # Vérifier si l'ID est valide
        execution = get_object_or_404(PrescriptionExecution, id=execution_id)

        if execution.status != 'Pending':
            messages.warning(request, "Cette exécution a déjà été marquée comme prise ou manquée.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        # Déterminer l'heure réelle d'exécution
        execution_time = now()
        execution.status = "Taken"
        execution.executed_at = execution_time
        execution.executed_by = request.user.employee  # Associer l'utilisateur qui a marqué l'exécution
        execution.save()

        # ✅ Ajuster les exécutions suivantes en fonction du retard
        adjust_future_executions(execution)

        messages.success(request,
                         "Exécution marquée comme prise avec succès. Les prochaines exécutions ont été ajustées.")
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


# @login_required
# def add_diagnostic(request, hospitalisation_id):
#     hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
#
#     if request.method == 'POST':
#         form = DiagnosticForm(request.POST)
#         if form.is_valid():
#             diagnostic = form.save(commit=False)
#             diagnostic.hospitalisation = hospitalisation
#             diagnostic.date_diagnostic = timezone.now()
#             diagnostic.medecin_responsable = request.user
#             diagnostic.save()  # Sauvegarde finale du diagnostic
#             # messages.success(request, f"Diagnostic '{diagnostic.nom}' ajouté avec succès.")
#             # return redirect('hospitalisationdetails', pk=hospitalisation_id)
#         else:
#             # Afficher les erreurs du formulaire avec un message d'erreur global
#             # messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
#             # return redirect('hospitalisationdetails', pk=hospitalisation_id)
#             return JsonResponse({'success': False, 'errors': form.errors}, status=400)
#
#
#     # Pour les requêtes GET (peu probable dans ce cas), rediriger
#     messages.error(request, "Méthode non autorisée.")
#     return redirect('hospitalisationdetails', pk=hospitalisation_id)

@login_required
def add_diagnostic(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)

    if request.method == 'POST':
        data = request.POST.copy()

        # Vérifiez si la maladie existe, sinon créez-la
        maladie_nom = data.get('maladie')
        if maladie_nom and not Maladie.objects.filter(nom=maladie_nom).exists():
            nouvelle_maladie = Maladie.objects.create(nom=maladie_nom)
            data['maladie'] = nouvelle_maladie.id  # Remplacez le nom par l'ID dans les données POST

        form = DiagnosticForm(data)
        if form.is_valid():
            diagnostic = form.save(commit=False)
            diagnostic.hospitalisation = hospitalisation
            diagnostic.date_diagnostic = timezone.now()
            diagnostic.medecin_responsable = request.user
            diagnostic.save()
            messages.success(request, f"Diagnostic '{diagnostic.nom}' ajouté avec succès.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)

    messages.error(request, "Méthode non autorisée.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@csrf_exempt
def add_maladie(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        if not nom:
            return JsonResponse({'success': False, 'message': 'Le nom de la maladie est requis.'})

        maladie, created = Maladie.objects.get_or_create(nom=nom)
        if created:
            return JsonResponse({'success': True, 'id': maladie.id, 'nom': maladie.nom})
        else:
            return JsonResponse({'success': False, 'message': 'Cette maladie existe déjà.'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})


def generate_unique_code_barre():
    """ Génère un code-barre unique de 12 chiffres. """
    while True:
        code = str(random.randint(10 ** 11, 10 ** 12 - 1))
        if not Medicament.objects.filter(codebarre=code).exists():
            return code


logger = logging.getLogger(__name__)


#noouveau code pour alpine
def search_medications(request):
    query = request.GET.get('q', '')
    if query:
        medications = Medicament.objects.filter(nom__icontains=query).values('id', 'nom', 'dosage_form', 'dosage',
                                                                             'unitdosage')

        return JsonResponse(list(medications), safe=False)
    return JsonResponse([], safe=False)


def parse_medication_data(medication_str):
    """
    Analyse la chaîne saisie par l'utilisateur et extrait :
    - nom : Nom du médicament
    - dosage : Quantité numérique
    - unitdosage : Unité de dosage (mg, ml, g, etc.)
    - dosage_form : Forme pharmaceutique (comprimé, gélule, etc.)
    """
    try:
        # Séparer la chaîne en mots
        words = medication_str.split()

        # Vérifier si le dernier mot est une unité de dosage connue
        known_units = ["mg", "g", "ml", "mcg", "UI", "L", "meq", "µL", "µg", "cm³", "mL/kg", "mg/m²", "mg/kg", "g/L"]
        known_forms = ["comprime", "gelule", "sirop", "injection", "ampoule", "pommade", "creme", "spray", "gouttes",
                       "patch",
                       "inhalateur",
                       "solution",
                       "suspension",
                       "poudre",
                       "ovule",
                       "collyre",
                       "aérosol",
                       "elixir",
                       "baume",
                       "granulé",
                       "capsule"]

        name_parts = []
        dosage = None
        unitdosage = None
        dosage_form = None

        for word in words:
            if word.isdigit():  # Vérifie si c'est un chiffre (dosage)
                dosage = int(word)
            elif word in known_units:  # Vérifie si c'est une unité de dosage
                unitdosage = word
            elif word in known_forms:  # Vérifie si c'est une forme pharmaceutique
                dosage_form = word
            else:
                name_parts.append(word)  # Fait partie du nom du médicament

        # Reconstruire le nom du médicament
        nom = " ".join(name_parts)

        logger.info(f"🔍 Médicament analysé : Nom={nom}, Dosage={dosage}, Unité={unitdosage}, Forme={dosage_form}")
        return nom, dosage, unitdosage, dosage_form

    except Exception as e:
        logger.error(f"⚠️ Erreur lors de l'analyse du médicament : {str(e)}")
        return medication_str, None, None, None  # Retourner la valeur brute si erreur


@csrf_exempt
@login_required  # ✅ Assurez-vous que l'utilisateur est connecté
# ✅ Assurez-vous que l'utilisateur est connecté
def add_prescription(request):
    if request.method == 'POST':
        try:
            logger.info("🔵 Données reçues: %s", request.POST)

            data = request.POST
            patient_id = data.get('patient_id')  # ✅ Récupération du patient
            hospitalisation_id = data.get('hospitalisation_id')  # ✅ Récupération de l'hospitalisation
            medication_name = data.get('medication', '').strip()
            quantity = data.get('quantity', '').strip()
            posology = data.get('posology', '').strip()
            pendant = data.get('pendant', '').strip()
            a_partir_de = data.get('a_partir_de', '').strip()
            is_new = data.get('is_new_medication', 'false') == 'true'

            # ✅ Récupérer le docteur via `request.user`
            try:
                doctor = Employee.objects.get(user=request.user)
                created_by = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Docteur non trouvé pour cet utilisateur'}, status=400)
            print(f'created{doctor}')
            # 🛑 Vérification des champs obligatoires
            if not patient_id:
                return JsonResponse({'success': False, 'error': 'Le patient est obligatoire'}, status=400)
            if not medication_name:
                return JsonResponse({'success': False, 'error': 'Le médicament est obligatoire'}, status=400)
            if not quantity:
                return JsonResponse({'success': False, 'error': 'La quantité est obligatoire'}, status=400)

            # 🔍 Vérification et récupération du patient
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Patient introuvable'}, status=400)

            # 🔍 Vérification et récupération de l'hospitalisation (optionnel)
            hospitalisation = None
            if hospitalisation_id:
                try:
                    hospitalisation = Hospitalization.objects.get(id=hospitalisation_id)
                except Hospitalization.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Hospitalisation introuvable'}, status=400)

            # 🔍 Vérification de la quantité (doit être un nombre positif)
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    return JsonResponse({'success': False, 'error': 'La quantité doit être un nombre positif'},
                                        status=400)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Quantité invalide'}, status=400)

            # ✅ Extraction des informations du médicament
            nom, dosage, unitdosage, dosage_form = parse_medication_data(medication_name)

            # 🔄 Création ou récupération du médicament avec les valeurs bien séparées
            if is_new:
                medication, created = Medicament.objects.get_or_create(
                    nom=nom,
                    defaults={'dosage': dosage, 'unitdosage': unitdosage, 'dosage_form': dosage_form}
                )
                logger.info("🟢 Nouveau médicament enregistré: %s (ID: %s)", medication.nom, medication.id)
            else:
                medication = Medicament.objects.filter(nom=nom).first()
                if not medication:
                    logger.warning("⚠️ Médicament introuvable: %s, enregistrement en tant que nouveau", nom)
                    medication, created = Medicament.objects.get_or_create(
                        nom=nom,
                        defaults={'dosage': dosage, 'unitdosage': unitdosage, 'dosage_form': dosage_form}
                    )

            # 📝 Création de la prescription avec patient, docteur et hospitalisation
            with transaction.atomic():
                prescription = Prescription.objects.create(
                    patient=patient,
                    doctor=doctor,  # ✅ Ajout du docteur connecté
                    created_by=created_by,  # ✅ Ajout du docteur connecté
                    hospitalisation=hospitalisation,  # ✅ Ajout de l'hospitalisation
                    medication=medication,
                    quantity=quantity,
                    posology=posology,
                    pendant=pendant,
                    a_partir_de=a_partir_de,
                    status="Pending"
                )

                # ✅ Exécuter `generate_executions()` immédiatement après l'ajout
                prescription.generate_executions()

            logger.info("✅ Prescription enregistrée avec succès: ID %s", prescription.id)
            return JsonResponse({'success': True, 'prescription_id': prescription.id})

        except Exception as e:
            logger.error("❌ ERREUR LORS DE L'ENREGISTREMENT DE LA PRESCRIPTION: %s", str(e))
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


def validate_and_create_medicament(request):
    if request.method == 'POST':
        new_medicament = request.session.get('new_medicament')
        if not new_medicament:
            return JsonResponse({'success': False, 'message': 'Aucun médicament en attente de validation.'}, status=400)

        medicament = Medicament.objects.create(
            nom=new_medicament['nom'],
            codebarre=new_medicament['codebarre']
        )

        del request.session['new_medicament']  # Nettoyer la session après création
        return JsonResponse(
            {'success': True, 'id': medicament.id, 'nom': medicament.nom, 'codebarre': medicament.codebarre})

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)


@login_required
def add_observations(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = ObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.hospitalisation = hospitalisation
            observation.patient = hospitalisation.patient
            # observation.date_enregistrement = timezone.now()  # Utilisation correcte du champ dans le modèle
            observation.medecin = request.user  # Associe l'utilisateur actuel comme médecin
            observation.save()
            messages.success(request, "Observation ajoutée avec succès.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout de l'observation. Veuillez corriger les erreurs.")

    messages.error(request, "Erreur lors de l'ajout de l'observation. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_avis_medical(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = AvisMedicalForm(request.POST)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.hospitalisation = hospitalisation
            avis.date_avis = timezone.now()
            avis.medecin = request.user
            avis.save()
            messages.success(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
    else:
        form = AvisMedicalForm()
    messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_hospi_comment(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)

    if request.method == 'POST':
        form = CommentaireInfirmierForm(request.POST)
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.patient = hospitalisation.patient
            commentaire.hospitalisation = hospitalisation
            commentaire.medecin = request.user
            commentaire.save()
            messages.success(request, "Commentaire ajouté avec succès.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout du commentaire. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CommentaireInfirmierForm()
    messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_effet_indesirable(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = EffetIndesirableForm(request.POST)
        if form.is_valid():
            try:
                effet = form.save(commit=False)
                effet.hospitalisation = hospitalisation
                effet.patient = hospitalisation.patient
                effet.medecin = request.user
                effet.save()
                messages.success(request, "Effet indésirable ajouté avec succès !")
                return redirect('hospitalisationdetails', pk=hospitalisation_id)
            except Exception as e:
                # Capture et affichage des exceptions inattendues
                messages.error(request, f"Une erreur inattendue s'est produite : {e}")
                traceback.print_exc()  # Afficher la trace complète dans la console pour le débogage
        else:
            # Récupérer et afficher les erreurs spécifiques du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans {field} : {error}")
    else:
        form = EffetIndesirableForm()
    messages.error(request, "Erreur. Veuillez corriger les erreurs ci-dessous.")

    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_historique_maladie(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = HistoriqueMaladieForm(request.POST)
        if form.is_valid():
            historique = form.save(commit=False)
            historique.hospitalisation = hospitalisation
            historique.medecin = request.user  # Associe le médecin connecté
            historique.save()
            messages.success(request, "Historique de la maladie ajouté avec succès.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout de l'historique. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = HistoriqueMaladieForm()
    messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


def ajouter_mode_de_vie(request, hospitalisation_id):
    """Vue pour ajouter un mode de vie à un patient"""
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("categorie_"):
                _, index, idx = key.split("_")  # Récupérer les index du champ
                categorie_id = request.POST.get(f"categorie_{index}_{idx}")
                description = request.POST.get(f"description_{index}_{idx}")
                frequence = request.POST.get(f"frequence_{index}_{idx}")
                impact = request.POST.get(f"impact_{index}_{idx}")

                if categorie_id and description:
                    categorie_obj = ModeDeVieCategorie.objects.get(pk=categorie_id)
                    mode_de_vie = ModeDeVie(
                        patient=hospitalisation.patient,
                        categorie=categorie_obj,
                        description=description,
                        frequence=frequence if frequence else None,
                        niveau_impact=impact if impact else None,
                        created_by=request.user.employee
                    )
                    mode_de_vie.save()

        messages.success(request, "Le mode de vie a été ajouté avec succès.")
        return redirect('hospitalisationdetails', pk=hospitalisation_id)  # Redirection après soumission

    messages.error(request, "Erreur lors de l'ajout du diagnostic. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_antecedents_hospi(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("type_"):
                _, index, idx = key.split("_")  # Récupérer les index du champ
                type_id = request.POST.get(f"type_{index}_{idx}")
                nom = request.POST.get(f"nom_{index}_{idx}")
                descriptif = request.POST.get(f"descriptif_{index}_{idx}")
                date_debut = request.POST.get(f"date_debut_{index}_{idx}")

                if nom and type_id:
                    type_obj = TypeAntecedent.objects.get(pk=type_id)
                    antecedent = AntecedentsMedicaux(
                        hospitalisation_id=hospitalisation_id,
                        type=type_obj,
                        nom=nom,
                        descriptif=descriptif,
                        date_debut=date_debut if date_debut else None,
                        patient=hospitalisation.patient,

                    )
                    antecedent.save()
        messages.success(request, "Antecedents ajoutes avec succes.")
        return redirect('hospitalisationdetails', pk=hospitalisation_id)  # Redirection après soumission

    # Reprendre le contexte avec les types pour l'affichage du formulaire
    messages.error(request, "Erreur. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_examen_apareil(request, hospitalisation_id):
    """Ajoute un examen d'appareil pour une hospitalisation donnée."""
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)

    if request.method == "POST":
        appareils_ajoutes = 0
        erreurs_detectees = []

        print("📥 Données reçues du formulaire :", request.POST)  # ✅ Debugging

        # ✅ Utilisation d'une REGEX pour capturer les bons index
        pattern = re.compile(r"type_appareil_(\d+)_(\d+)")

        for key, value in request.POST.items():
            match = pattern.match(key)  # ✅ Vérifier si la clé suit le bon format

            if match:
                try:
                    index, idx = match.groups()  # ✅ Extraction des indices numériques

                    # Récupération et nettoyage des valeurs
                    type_id = request.POST.get(f"type_appareil_{index}_{idx}", "").strip()
                    nom = request.POST.get(f"nom_{index}_{idx}", "").strip()
                    etat = request.POST.get(f"etat_{index}_{idx}", "normal").strip()
                    observation = request.POST.get(f"observation_{index}_{idx}", "").strip()

                    # 🚨 Vérification des entrées vides
                    if not type_id or not nom:
                        erreurs_detectees.append(
                            f"⚠️ Données incomplètes pour {key} (Type: {type_id}, Nom: {nom}) - Ignoré")
                        continue  # ✅ Ignore cette entrée sans erreur fatale

                    print(
                        f"🔄 Traitement : Type: {type_id}, Nom: {nom}, État: {etat}, Observation: {observation}")  # ✅ Debugging

                    # Récupérer l'objet `AppareilType`
                    type_obj = get_object_or_404(AppareilType, pk=int(type_id))

                    # ✅ Vérifier si un appareil avec ce nom et cette hospitalisation existe déjà
                    if Appareil.objects.filter(hospitalisation=hospitalisation, nom=nom).exists():
                        erreurs_detectees.append(
                            f"⚠️ L'appareil '{nom}' existe déjà pour cette hospitalisation - Ignoré.")
                        continue  # ✅ Ignore cette entrée sans erreur fatale

                    # ✅ Création d'un nouvel appareil
                    Appareil.objects.create(
                        type_appareil=type_obj,
                        hospitalisation=hospitalisation,
                        nom=nom,
                        etat=etat,
                        observation=observation
                    )

                    appareils_ajoutes += 1  # ✅ Incrémenter seulement si l'ajout a réussi

                except ValueError as e:
                    erreurs_detectees.append(f"❌ Erreur ValueError sur {key} - {str(e)}")
                except Exception as e:
                    erreurs_detectees.append(f"❌ Erreur générale sur {key} - {str(e)}")

        print(f"✅ Appareils ajoutés : {appareils_ajoutes}")
        if erreurs_detectees:
            print(f"⚠️ Erreurs détectées : {erreurs_detectees}")

        if appareils_ajoutes > 0:
            messages.success(request, f"✅ {appareils_ajoutes} nouvel(s) examen(s) des appareils ajouté(s) avec succès.")
        else:
            messages.error(request, "⚠️ Aucun appareil enregistré. Vérifiez les données du formulaire.")

        return redirect('hospitalisationdetails', pk=hospitalisation_id)

    messages.error(request, "❌ Erreur lors de l'ajout de l'examen.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_resume_syndromique(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = ResumeSyndromiqueForm(request.POST)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.patient = hospitalisation.patient
            resume.hospitalisation = hospitalisation
            resume.created_by = request.user.employee  # Associe le médecin connecté
            resume.save()
            messages.success(request, "Résumé  ajouté avec succès.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout du Résumé. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = HistoriqueMaladieForm()
    messages.error(request, "Erreur lors de l'ajout du Résumé. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@login_required
def add_problemes_pose(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    if request.method == 'POST':
        form = ProblemePoseForm(request.POST)
        if form.is_valid():
            probleme = form.save(commit=False)
            probleme.patient = hospitalisation.patient
            probleme.hospitalisation = hospitalisation
            probleme.created_by = request.user.employee  # Associe le médecin connecté
            probleme.save()
            messages.success(request, "Problemes ajouté avec succès.")
            return redirect('hospitalisationdetails', pk=hospitalisation_id)
        else:
            messages.error(request, "Erreur lors de l'ajout du Problemes. Veuillez corriger les erreurs ci-dessous.")
    else:
        form = HistoriqueMaladieForm()
    messages.error(request, "Erreur lors de l'ajout du Problemes. Veuillez corriger les erreurs ci-dessous.")
    return redirect('hospitalisationdetails', pk=hospitalisation_id)


@csrf_exempt  # Désactive CSRF pour tester (à sécuriser avec le token dans les headers)
def update_execution_status(request):
    """
    Vue pour mettre à jour le statut d'une PrescriptionExecution.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            execution_id = data.get("execution_id")
            new_status = data.get("new_status")

            execution = PrescriptionExecution.objects.get(id=execution_id)

            # Vérifie que l'exécution est bien en attente et que le temps est dépassé
            if execution.status == "Pending" and execution.scheduled_time < now():
                execution.status = new_status
                execution.save()
                return JsonResponse({"success": True, "message": "Mise à jour effectuée."})
            else:
                return JsonResponse({"success": False, "message": "Statut non modifié."}, status=400)

        except PrescriptionExecution.DoesNotExist:
            return JsonResponse({"success": False, "message": "Exécution introuvable."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Requête invalide."}, status=400)

    return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)


@login_required
def add_bilan_paraclinique(request, hospitalisation_id):
    """
    Vue pour enregistrer les examens sélectionnés dans un bilan paraclinique.
    """
    if request.method == "POST":
        examens_ids = request.POST.getlist("examens")  # Récupérer la liste des examens sélectionnés
        hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
        patient = hospitalisation.patient

        if not examens_ids:
            return JsonResponse({'success': False, 'message': "Aucun examen sélectionné."}, status=400)

        try:
            for examen_id in examens_ids:
                examen = get_object_or_404(ExamenStandard, id=examen_id)
                BilanParaclinique.objects.create(
                    patient=patient,
                    hospitalisation=hospitalisation,
                    examen=examen,
                    doctor=request.user.employee
                )
            return JsonResponse({'success': True, 'message': "Bilans ajoutés avec succès."})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Erreur: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': "Méthode non autorisée."}, status=405)


@login_required
def add_imagerie(request, hospitalisation_id):
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    patient = hospitalisation.patient

    if request.method == "POST":
        form = ImagerieMedicaleForm(request.POST, request.FILES)
        if form.is_valid():
            imagerie = form.save(commit=False)
            imagerie.patient = patient
            imagerie.hospitalisation = hospitalisation
            imagerie.medecin_prescripteur = request.user
            imagerie.save()
            messages.success(request, "Imagerie enregistrée avec succès.")
            return redirect("hospitalisationdetails", pk=hospitalisation_id)
    else:
        form = ImagerieMedicaleForm()

    return render(request, "pages/imagerie/add_imagerie.html", {"form": form, "hospitalisation": hospitalisation})


def generate_ordonnance_pdf(request, patient_id, hospitalisation_id):
    """
    Génère une ordonnance PDF pour un patient hospitalisé à partir de ses prescriptions.
    """
    # 🔍 Récupérer le patient, l'hospitalisation et ses prescriptions
    patient = get_object_or_404(Patient, id=patient_id)
    hospitalisation = get_object_or_404(Hospitalization, id=hospitalisation_id)
    prescriptions = Prescription.objects.filter(patient=patient, hospitalisation=hospitalisation).order_by(
        'prescribed_at')

    # 📄 Configuration du PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ordonnance_{patient.nom}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # 📌 Ajout d'un en-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Ordonnance Médicale")

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Patient : {patient.nom} {patient.prenoms}")
    p.drawString(100, height - 100,
                 f"Date : {prescriptions.first().prescribed_at.strftime('%d/%m/%Y') if prescriptions else 'N/A'}")

    p.drawString(100, height - 120, f"Hôpital : {hospitalisation if hospitalisation else 'Non précisé'}")

    # Ajout du médecin prescripteur
    doctor = prescriptions.first().doctor if prescriptions else None
    p.drawString(100, height - 140, f"Médecin : {doctor.nom if doctor else 'Inconnu'}")

    # 📌 Lignes de séparation
    p.line(100, height - 150, 500, height - 150)

    # 📌 Génération des prescriptions
    y_position = height - 180
    p.setFont("Helvetica", 11)

    for prescription in prescriptions:
        text = f"- {prescription.medication.nom} ({prescription.medication.dosage_form} {prescription.medication.dosage} {prescription.medication.unitdosage})"
        text += f" | Posologie : {prescription.posology} | Pendant : {prescription.pendant} jours"

        # Vérification de l'espace sur la page
        if y_position < 50:
            p.showPage()
            p.setFont("Helvetica", 11)
            y_position = height - 50  # Nouvelle page, recommencer en haut

        p.drawString(100, y_position, text)
        y_position -= 20

    # 📌 Fin du document
    p.showPage()
    p.save()

    return response


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
        # Charger tous les types d'antécédents sous forme de liste de dictionnaires
        types_antecedents = list(TypeAntecedent.objects.values("id", "nom"))
        context['types_antecedents_json'] = json.dumps(types_antecedents, cls=DjangoJSONEncoder)
        context['antecedentshospi'] = AntecedentsHospiForm()

        # Récupérer les catégories de mode de vie
        categorie_modedevie = list(ModeDeVieCategorie.objects.values("id", "nom"))
        context['categorie_modedevie_json'] = json.dumps(categorie_modedevie, cls=DjangoJSONEncoder)
        context['modedevieform'] = ModeDeVieForm()

        # Charger les types d'appareils avec leurs sous-types
        types_parents = AppareilType.objects.filter(parent__isnull=True).prefetch_related('sous_types_appareil')

        # Convertir les données en JSON pour Alpine.js
        types_appareils = [
            {
                "id": type_.id,
                "nom": type_.nom,
                "sous_types": [{"id": sous_type.id, "nom": sous_type.nom} for sous_type in
                               type_.sous_types_appareil.all()]
            }
            for type_ in types_parents
        ]

        # Passer les données JSON au template
        context['types_appareils_json'] = json.dumps(types_appareils, cls=DjangoJSONEncoder)

        # Récupérer tous les types de bilans avec leurs examens associés
        types_examens = TypeBilanParaclinique.objects.prefetch_related('examenstandard_set').all()

        # Transformer les données pour Alpine.js
        types_examens_json = [
            {
                "id": type_bilan.id,
                "nom": type_bilan.nom,
                "examens": [{"id": exam.id, "nom": exam.nom} for exam in type_bilan.examenstandard_set.all()]
            }
            for type_bilan in types_examens
        ]

        # Ajouter les examens au contexte en format JSON
        context["types_examens_json"] = json.dumps(types_examens_json, ensure_ascii=False)
        context['bilanForm'] = BilanParacliniqueMultiForm()

        context['appareilForm'] = AppareilForm()
        context['problemesposerform'] = ProblemePoseForm()
        # context['antecedentshospigroup'] = GroupedAntecedentsForm()
        context['prescription_hospi_form'] = PrescriptionHospiForm()
        context['signe_fonctionnel_form'] = SigneFonctionnelForm()

        context['indicateur_biologique_form'] = IndicateurBiologiqueForm()
        context['indicateur_fonctionnel_form'] = IndicateurFonctionnelForm()
        context['indicateur_subjectif_form'] = IndicateurSubjectifForm()
        context['autresindicatorsform'] = HospitalizationIndicatorsForm()

        context['resumesyndromiqueform'] = ResumeSyndromiqueForm()

        context['diagnosticsform'] = DiagnosticForm()
        context['observationform'] = ObservationForm()
        context['avismedicalform'] = AvisMedicalForm()
        context['effetindesirableform'] = EffetIndesirableForm()
        context['historiquemaladieform'] = HistoriqueMaladieForm()
        context['hospicomment'] = CommentaireInfirmierForm()
        # context['antecedents'] = AntecedentsHospiForm()

        context['observations'] = Observation.objects.filter(hospitalisation=self.object).order_by(
            '-date_enregistrement')
        context['observationscount'] = Observation.objects.filter(hospitalisation=self.object).count

        context['historiques_maladie'] = HistoriqueMaladie.objects.filter(hospitalisation=self.object).order_by(
            '-date_enregistrement')

        # Récupérer tous les modes de vie liés à cette hospitalisation
        modedevies = ModeDeVie.objects.filter(hospitalisation=hospitalization).select_related('categorie')

        # Regrouper les modes de vie par catégorie
        modedevies_par_categorie = defaultdict(list)
        for modevie in modedevies:
            modedevies_par_categorie[modevie.categorie.nom].append(modevie)

        # Trier les catégories pour un affichage ordonné
        context['modedevies_by_categories'] = OrderedDict(sorted(modedevies_par_categorie.items()))
        context['modedevies_count'] = modedevies.count()

        # Regrouper les antécédents par type
        antecedents = AntecedentsMedicaux.objects.filter(hospitalisation=hospitalization)

        antecedents_par_type = defaultdict(list)
        for antecedent in antecedents:
            antecedents_par_type[antecedent.type.nom].append(antecedent)

        # Trier par type pour un affichage ordonné
        context['antecedents_par_type'] = dict(antecedents_par_type)
        context['antecedentscount'] = AntecedentsMedicaux.objects.filter(hospitalisation=self.object).count()

        context['diagnostics'] = Diagnostic.objects.filter(hospitalisation=self.object).order_by('-date_diagnostic')
        context['diagnosticscount'] = Diagnostic.objects.filter(hospitalisation=self.object).count()

        context['avis_medicaux'] = AvisMedical.objects.filter(hospitalisation=self.object).order_by('-date_avis')
        context['avis_medicauxcount'] = AvisMedical.objects.filter(hospitalisation=self.object).count()

        context['effets_indesirables'] = EffetIndesirable.objects.filter(hospitalisation=self.object).order_by(
            '-date_signalement')
        context['effets_indesirablescount'] = EffetIndesirable.objects.filter(hospitalisation=self.object).count()

        context['hopi_comment'] = CommentaireInfirmier.objects.filter(hospitalisation=self.object).order_by(
            '-date_commentaire')
        context['hopi_commentcount'] = CommentaireInfirmier.objects.filter(hospitalisation=self.object).count()

        context['constantes'] = Constante.objects.filter(hospitalisation=self.object)
        # Retrieve related 'Constante' data for the current hospitalization
        context['chart_data'] = json.dumps(data, cls=DjangoJSONEncoder)
        context['functional_chart_data'] = json.dumps(donnees, cls=DjangoJSONEncoder)
        context['complications_chart_data'] = json.dumps(complicbarre, cls=DjangoJSONEncoder)
        context['pie_chart_data'] = json.dumps(complic)
        context['lab_ink'] = json.dumps(labcompliq, cls=DjangoJSONEncoder)
        context['constantescharts'] = Constante.objects.filter(hospitalisation=self.object).order_by('created_at')
        context['prescriptions'] = Prescription.objects.filter(patient=self.object.patient).order_by('-created_at')
        context['suivie_prescriptions'] = Prescription.objects.filter(hospitalisation=hospitalization).order_by(
            '-created_at')
        prescriptions = Prescription.objects.filter(hospitalisation=hospitalization)
        executions = PrescriptionExecution.objects.filter(prescription__in=prescriptions,
                                                          scheduled_time__gte=now()).order_by('scheduled_time')
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
        missed_executions = executions.filter(scheduled_time__lt=now(), status='Missed'
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
