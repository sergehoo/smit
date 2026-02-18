import datetime
import json
import os
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime
from itertools import groupby

import django_filters
import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, AccessMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Avg, Prefetch, Q
from django.db.models.functions import ExtractMonth, ExtractYear
from django import forms
from django.http import request, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django_filters.views import FilterView

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus.tables import TableStyle, Table
from six import BytesIO

from core.models import communes_et_quartiers_choices, Location, VIHProfile
from core.utils.notifications import get_employees_to_notify
from core.utils.sms import send_sms
from pharmacy.models import RendezVous
from smit.filters import PatientFilter
from smit.forms import PatientCreateForm, AppointmentForm, ConstantesForm, ConsultationSendForm, ConsultationCreateForm, \
    SymptomesForm, ExamenForm, PrescriptionForm, AntecedentsMedicauxForm, AllergiesForm, ProtocolesForm, \
    ConseilsForm, HospitalizationSendForm, TestRapideVIHForm, EnqueteVihForm, ConsultationForm, EchantillonForm, \
    HospitalizationForm, AppointmentUpdateForm, SuiviSendForm, RdvSuiviForm, UrgencePatientForm, CasContactForm, \
    PatientUpdateForm, TraitementARVForm, SuiviProtocoleForm, RendezVousForm, BilanParacliniqueForm, \
    RendezVousSuiviForm, ProtocoleForm, UrgenceHospitalizationStep2Form
from smit.models import Patient, Appointment, Constante, Service, ServiceSubActivity, Consultation, Symptomes, \
    Hospitalization, Suivi, TestRapideVIH, EnqueteVih, Examen, Protocole, SuiviProtocole, TraitementARV, BilanInitial, \
    TypeBilanParaclinique, ExamenStandard, BilanParaclinique, Echantillon, ParaclinicalExam, ImagerieMedicale, \
    Prescription


# Create your views here.
# Vue API pour envoyer les données à ApexCharts en JSON
def hospitalization_chart_data(request):
    view = HomePageView()
    stats = view.get_hospitalization_statistics()
    return JsonResponse(stats, safe=False)


class Landing(TemplateView):
    # form_class = LoginForm
    template_name = "pages/landing.html"


# views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Count, Avg
from django.db.models.functions import ExtractMonth, ExtractYear

import json
from datetime import timedelta


# Importe tes modèles
# from .models import Patient, Consultation, Appointment, Hospitalization, Service

class HomePageView(LoginRequiredMixin, TemplateView):
    login_url = '/accounts/login/'
    template_name = "pages/home.html"

    # --------- Helpers ---------
    @staticmethod
    def _qs_to_list(qs):
        """Assure une liste de dicts sérialisable JSON."""
        return list(qs)

    @staticmethod
    def _json(data):
        """json.dumps avec accents conservés."""
        return json.dumps(data, ensure_ascii=False)

    # --------- Données auxiliaires ---------
    def get_patient_age_distribution(self):
        """
        Retourne le nombre de patients par tranche d'âge et sexe.
        """
        now = timezone.now()
        current_year = now.year

        age_groups = [
            ("0-18 ans", 0, 18),
            ("19-25 ans", 19, 25),
            ("26-35 ans", 26, 35),
            ("36-45 ans", 36, 45),
            ("46-60 ans", 46, 60),
            ("61-75 ans", 61, 75),
            ("75 ans et plus", 76, 120),
        ]
        age_distribution = {g[0]: {"Hommes": 0, "Femmes": 0} for g in age_groups}

        patients = Patient.objects.values('date_naissance', 'genre')
        for p in patients:
            dob = p.get('date_naissance')
            if not dob:
                continue
            age = current_year - dob.year
            genre = "Hommes" if p.get('genre') == "Homme" else "Femmes"
            for label, amin, amax in age_groups:
                if amin <= age <= amax:
                    age_distribution[label][genre] += 1
                    break
        return age_distribution

    def get_hospitalization_statistics(self):
        """
        Stats hospitalisations par période + global.
        """
        now = timezone.now()
        current_year = now.year

        periods = [
            ("Cette semaine", now - timedelta(days=7)),
            ("Ce mois", now.replace(day=1)),
            ("Cette année", timezone.datetime(current_year, 1, 1, tzinfo=now.tzinfo)),
        ]

        stats = []
        for label, start_date in periods:
            base = Hospitalization.objects.filter(admission_date__gte=start_date)
            total_hospitalized = base.count()
            total_deaths = base.filter(status="DCD").count()
            total_recovered = base.filter(status="Gueris-EXEA").count()
            total_transferred = base.filter(status="Transféré-TRANSF").count()
            total_scam = base.filter(status="SCAM").count()
            total_evade = base.filter(status="EVADE").count()
            death_rate = (total_deaths / total_hospitalized * 100) if total_hospitalized else 0

            stats.append({
                "periode": label,
                "total_hospitalized": total_hospitalized,
                "total_deaths": total_deaths,
                "total_recovered": total_recovered,
                "total_transferred": total_transferred,
                "total_scam": total_scam,
                "total_evade": total_evade,
                "death_rate": round(death_rate, 2),
            })

        total_hospitalized_all = Hospitalization.objects.count()
        total_deaths_all = Hospitalization.objects.filter(status="DCD").count()
        total_recovered_all = Hospitalization.objects.filter(status="Gueris-EXEA").count()
        total_transferred_all = Hospitalization.objects.filter(status="Transféré-TRANSF").count()
        total_scam_all = Hospitalization.objects.filter(status="SCAM").count()
        total_evade_all = Hospitalization.objects.filter(status="EVADE").count()
        global_death_rate = (total_deaths_all / total_hospitalized_all * 100) if total_hospitalized_all else 0

        stats.append({
            "periode": "Global",
            "total_hospitalized": total_hospitalized_all,
            "total_deaths": total_deaths_all,
            "total_recovered": total_recovered_all,
            "total_transferred": total_transferred_all,
            "total_scam": total_scam_all,
            "total_evade": total_evade_all,
            "death_rate": round(global_death_rate, 2),
        })
        return stats

    # --------- Contexte principal ---------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        current_year = now.year

        # Tendances patients (si utilisé ailleurs)
        monthly_patient_counts = (
            Patient.objects.filter(created_at__year=current_year)
            .annotate(month=ExtractMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_counts = [0] * 12
        for entry in monthly_patient_counts:
            monthly_counts[entry['month'] - 1] = entry['count']

        # Statistiques Patients
        total_patients = Patient.objects.count()
        total_patients_femme = Patient.objects.filter(genre='Femme').count()
        total_patients_homme = Patient.objects.filter(genre='Homme').count()
        patient_status_counts_qs = Patient.objects.values('status').annotate(count=Count('status'))
        avg_age = (
            Patient.objects
            .annotate(age=(ExtractYear(timezone.now()) - ExtractYear('date_naissance')))
            .aggregate(Avg('age'))
        )
        average_age = avg_age.get('age__avg') or 0

        # Services
        consultation_by_service_qs = Consultation.objects.values('services__nom').annotate(count=Count('id'))
        top_services = Service.objects.annotate(total_use=Count('consultations')).order_by('-total_use')[:5]
        recent_consultations = Consultation.objects.select_related('patient', 'services', 'doctor').order_by(
            '-consultation_date')[:10]

        # Rendez-vous
        total_scheduled_appointments = Appointment.objects.filter(status='Scheduled').count()
        appointment_status_counts_qs = Appointment.objects.values('status').annotate(count=Count('status'))
        upcoming_appointments = Appointment.objects.filter(date__gte=now.date()).order_by('date')[:10]

        # Hospitalisations
        current_hospitalizations = Hospitalization.objects.filter(discharge_date__isnull=True).count()
        hospitalizations_by_reason_qs = Hospitalization.objects.values('reason_for_admission').annotate(
            count=Count('id'))
        recent_hospitalizations = Hospitalization.objects.select_related('patient', 'doctor').order_by(
            '-admission_date')[:10]

        # Tendances mensuelles (consultations / rendez-vous)
        monthly_consultations = (
            Consultation.objects.filter(consultation_date__year=current_year)
            .annotate(month=ExtractMonth('consultation_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_appointments = (
            Appointment.objects.filter(date__year=current_year)
            .annotate(month=ExtractMonth('date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        consultation_counts = [0] * 12
        appointment_counts = [0] * 12
        for entry in monthly_consultations:
            consultation_counts[entry['month'] - 1] = entry['count']
        for entry in monthly_appointments:
            appointment_counts[entry['month'] - 1] = entry['count']

        # ---------- Sérialisations JSON sûres pour le template ----------
        # Noms cohérents avec le template fourni
        consultations_by_service_json = self._json([
            {"services__nom": row.get("services__nom") or "Inconnu", "count": row.get("count", 0)}
            for row in self._qs_to_list(consultation_by_service_qs)
        ])

        hospitalizations_by_reason_json = self._json([
            {"reason_for_admission": row.get("reason_for_admission") or "Inconnue", "count": row.get("count", 0)}
            for row in self._qs_to_list(hospitalizations_by_reason_qs)
        ])

        appointment_status_counts_json = self._json([
            {"status": row.get("status") or "Inconnu", "count": row.get("count", 0)}
            for row in self._qs_to_list(appointment_status_counts_qs)
        ])

        patient_status_counts_json = self._json([
            {"status": row.get("status") or "Inconnu", "count": row.get("count", 0)}
            for row in self._qs_to_list(patient_status_counts_qs)
        ])

        consultation_counts_json = self._json(consultation_counts or [])
        appointment_counts_json = self._json(appointment_counts or [])

        context.update({
            "current_time": now.strftime("%d/%m/%Y %H:%M"),
            "hospitalization_statistics": self.get_hospitalization_statistics(),
            "patient_age_distribution": self.get_patient_age_distribution(),
            "monthly_counts": monthly_counts,

            "total_patients": total_patients,
            "total_patients_femme": total_patients_femme,
            "total_patients_homme": total_patients_homme,
            "average_age": average_age,

            "consultation_by_service": consultation_by_service_qs,
            "top_services": top_services,
            "recent_consultations": recent_consultations,

            "total_scheduled_appointments": total_scheduled_appointments,
            "upcoming_appointments": upcoming_appointments,

            "current_hospitalizations": current_hospitalizations,
            "hospitalizations_by_reason": hospitalizations_by_reason_qs,
            "recent_hospitalizations": recent_hospitalizations,

            "consultation_counts": consultation_counts,  # encore dispo si ailleurs
            "appointment_counts": appointment_counts,  # idem

            # Blobs JSON pour le template (charts)
            "consultations_by_service_json": consultations_by_service_json,
            "hospitalizations_by_reason_json": hospitalizations_by_reason_json,
            "appointment_status_counts_json": appointment_status_counts_json,
            "patient_status_counts_json": patient_status_counts_json,
            "consultation_counts_json": consultation_counts_json,
            "appointment_counts_json": appointment_counts_json,
        })
        return context


@login_required
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.status = 'Scheduled'
            form.save()
            messages.success(request, 'Rendez-vous créé avec succès!')
            return redirect('appointment_list')
        else:
            messages.error(request, 'Le rendez-vous na pas ete créé!')

    else:
        form = AppointmentForm()
        return render(request, 'pages/appointments/appointment_form.html', {'form': form})


# @login_required
# def consultation_send_create(request, patient_id):
#     patient = get_object_or_404(Patient, id=patient_id)
#     if request.method == 'POST':
#         form = ConsultationSendForm(request.POST)
#         if form.is_valid():
#
#             consultation = form.save(commit=False)
#             consultation.patient = patient
#             consultation.created_by = request.user.employee
#             consultation.services = form.cleaned_data['service']
#             consultation.activite = 'Consultation'
#             form.save()
#             messages.success(request, 'Patient transféré en consultation avec succès!')
#             return redirect('attente')
#     else:
#         messages.error(request, 'Le transfert na pas ete effectue!')
#         form = ConsultationSendForm()
#     return redirect('attente')
@login_required
def consultation_send_create(request, patient_id, rdv_id):
    patient = get_object_or_404(Patient, id=patient_id)
    appointment = get_object_or_404(Appointment, id=rdv_id)
    if request.method == 'POST':
        form = ConsultationSendForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.created_by = request.user.employee
            consultation.status = 'Scheduled'

            # Ensure 'service' is correctly handled
            service = form.cleaned_data['service']
            consultation.services = service

            # Set the correct activity (assuming the activity is Consultation)
            activite = ServiceSubActivity.objects.filter(service=service, nom='Consultation').first()
            consultation.activite = activite

            # Update the status of the appointment to 'Completed'
            appointment.status = 'Completed'
            appointment.save()

            consultation.save()
            messages.success(request, 'Patient transféré en consultation avec succès!')
            return redirect('attente')
        else:
            messages.error(request, 'Le formulaire est invalide. Veuillez vérifier les informations.')
    else:
        form = ConsultationSendForm()

    context = {
        'form': form,
        'patient': patient,
    }
    return redirect('attente')


@login_required
def create_consultation_pdf(request, patient_id, consultation_id):
    # Récupérer la consultation et l'enquête VIH associée
    consultation = get_object_or_404(Consultation, id=consultation_id)
    patient = consultation.patient
    doctor = consultation.doctor if consultation.doctor else 'Inconnu'
    enquete_vih = EnqueteVih.objects.filter(consultation=consultation).first()

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="Fiche_de_bilan_initial_{consultation_id}_Patient_{patient.nom}.pdf"'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)  # Mode portrait

    # Charger les images
    logo_path = os.path.join(settings.STATIC_ROOT, 'images/logoMSHPCMU.jpg')
    logo_ci = os.path.join(settings.STATIC_ROOT, 'images/armoirieci.jpg')
    watermark_path = os.path.join(settings.STATIC_ROOT, 'images/bluefondsbilaninit.png')
    logo_image = ImageReader(logo_path) if os.path.exists(logo_path) else None
    logo_ci = ImageReader(logo_ci) if os.path.exists(logo_ci) else None
    watermark_image = ImageReader(watermark_path) if os.path.exists(watermark_path) else None

    # Générer un QR code avec des informations de la consultation
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr_data = f"Consultation ID: {consultation_id} - Patient: {patient.nom}- Code Patient: {patient.code_patient}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_image = ImageReader(qr_buffer)

    # Dimensions de la page A4
    width, height = A4

    # Dessiner le filigrane en arrière-plan
    if watermark_image:
        c.saveState()
        c.setFillAlpha(0.2)  # Ajustez la transparence du filigrane ici
        c.drawImage(watermark_image, 0, 0, width=width, height=height, mask='auto')
        c.restoreState()

    # Ajouter le logo en haut à gauche
    if logo_image:
        c.drawImage(logo_image, 2.5 * cm, height - 2 * cm, width=50, height=50)

    if logo_ci:
        c.drawImage(logo_ci, 16 * cm, height - 2 * cm, width=100, height=50)

    # Ajouter le QR code en bas à droite
    c.drawImage(qr_image, width - 4 * cm, 1 * cm, width=50, height=50)

    # Ajouter l'en-tête
    c.setFont("Helvetica", 8)
    c.drawString(1 * cm, height - 2.3 * cm, "Ministère de la Santé de l'hygiène Publique")  # Texte à gauche
    c.drawString(1 * cm, height - 2.6 * cm, "et de la Couverture Maladie Universelle")  # Texte à gauche

    c.drawString(2 * cm, height - 3 * cm, "___________________")  # Texte à gauche
    c.drawString(16.2 * cm, height - 2.3 * cm, "Union - Discipline - Travail")  # Texte à droite

    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.7 * cm, height - 3.5 * cm, "PNPCPVVIH/SIDA")  # Texte à gauche
    # c.drawString(16 * cm, height - 2 * cm, "République de Côte d'Ivoire")  # Texte à droite

    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.5 * cm, height - 5 * cm,
                 "FICHE DE BILAN INITIAL POUR LA PRISE EN CHARGE DES PERSONNES VIVANT AVEC LE VIH")  # Texte à droite
    c.line(1.5 * cm, height - 5.2 * cm, width - 1.8 * cm, height - 5.2 * cm)

    # Ajouter une ligne pour séparer l'en-tête du contenu
    # c.line(1 * cm, height - 2.2 * cm, width - 1 * cm, height - 2.2 * cm)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(0.4 * cm, height - 6 * cm, "I.")  # Texte à gauche
    c.drawString(1.5 * cm, height - 6 * cm, "Caractéristiques socio-démographiques du patient")  # Texte à gauche

    c.setFont("Helvetica-Bold", 8)

    c.drawString(2.5 * cm, height - 7 * cm, "DEM 01")  # Texte à gauche
    c.drawString(2.5 * cm, height - 7.5 * cm, "DEM 02")  # Texte à gauche
    c.drawString(2.5 * cm, height - 8 * cm, "DEM 03")  # Texte à gauche
    c.drawString(2.5 * cm, height - 8.5 * cm, "DEM 04")  # Texte à gauche
    c.drawString(2.5 * cm, height - 9 * cm, "DEM 05")  # Texte à gauche

    c.drawString(2.5 * cm, height - 14 * cm, "DEM 06")  # Texte à gauche
    c.drawString(2.5 * cm, height - 14.5 * cm, "DEM 08")  # Texte à gauche
    c.drawString(2.5 * cm, height - 15 * cm, "DEM 09")  # Texte à gauche
    c.drawString(2.5 * cm, height - 15.5 * cm, "DEM 10")  # Texte à gauche
    c.drawString(2.5 * cm, height - 16 * cm, "DEM 11")  # Texte à gauche
    c.drawString(2.5 * cm, height - 16.5 * cm, "DEM 12")  # Texte à gauche
    c.drawString(2.5 * cm, height - 17 * cm, "DEM 13")  # Texte à gauche
    c.drawString(2.5 * cm, height - 17.5 * cm, "DEM 14")  # Texte à gauche
    c.drawString(2.5 * cm, height - 18 * cm, "DEM 15")  # Texte à gauche

    c.setFont("Helvetica", 8)
    c.drawString(0.4 * cm, height - 7 * cm, "(DINTV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 7.5 * cm, "(SUJETNO)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 8 * cm, "(LABNO)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 8.5 * cm, "(NOMSERV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 9 * cm, "(SERVICE)")  # Texte à gauche

    c.drawString(0.4 * cm, height - 14 * cm, "(NOM)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 14.5 * cm, "(PRENOM)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 15 * cm, "(SEXE)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 15.5 * cm, "(DATENAIS)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 16 * cm, "(SESNIVET)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 16.5 * cm, "(SESETCV1)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 17 * cm, "(NATIONAL)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 17.5 * cm, "(RESIDE)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 18 * cm, "(NOMMED)")  # Texte à gauche

    c.setFont("Helvetica-Bold", 8)
    c.drawString(0.4 * cm, height - 19 * cm, "II.")  # Texte à gauche
    c.drawString(1.5 * cm, height - 19 * cm, "Données clinique")  # Texte à gauche

    c.setFont("Helvetica", 8)
    c.drawString(0.4 * cm, height - 19.5 * cm, "(HISATCD)")  # Texte à gauche
    c.drawString(2.5 * cm, height - 19.5 * cm, "CLI 01.")  # Texte à gauche
    c.drawString(5 * cm, height - 19.5 * cm, "Antécédents ")  # Texte à gauche

    c.drawString(0.4 * cm, height - 20.5 * cm, "(HISPRARRV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 21 * cm, "(HISPRTYP)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 21.5 * cm, "(HISTXARV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 22 * cm, "(HISTRARV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 22.5 * cm, "(DERXARV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 23 * cm, "(COTRIMO)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 23.5 * cm, "(STAEVOL)")  # Texte à gauche

    c.drawString(0.4 * cm, height - 24 * cm, "(IOENCOUR)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 24.54 * cm, "(TRAITIO)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 25 * cm, "(PHYPOIDS)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 25.5 * cm, "(PHYKARN)")  # Texte à gauche

    c.setFont("Helvetica", 8)

    c.drawString(2.5 * cm, height - 20.5 * cm, "CLI 02.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 21 * cm, "CLI 03.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 21.5 * cm, "CLI 04.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 22 * cm, "CLI 05.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 22.5 * cm, "CLI 06.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 23 * cm, "CLI 07.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 23.5 * cm, "CLI 08.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 24 * cm, "CLI 09.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 24.5 * cm, "CLI 10.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 25 * cm, "CLI 11.")  # Texte à gauche
    c.drawString(2.5 * cm, height - 25.5 * cm, "CLI 12.")  # Texte à gauche

    # Position de départ pour le formulaire
    y_position = height - 7 * cm
    line_height = 0.5 * cm

    # Fonction pour dessiner une ligne de formulaire avec pointillés
    c.setFont("Helvetica", 8)

    def draw_form_line(label, value):
        nonlocal y_position
        c.drawString(4 * cm, y_position, f"{label}")
        c.drawString(13 * cm, y_position, str(value) if value else '______________________________')
        c.setDash(1, 2)  # Pointillé
        c.line(9 * cm, y_position - 0.2 * cm, width - 2 * cm, y_position - 0.2 * cm)
        c.setDash()  # Réinitialiser les lignes normales
        y_position -= line_height

    # Informations de la consultation sous forme de lignes de formulaire
    draw_form_line("Date de l'interview ", patient.code_vih)
    draw_form_line("Sujet No ", patient.nom)
    draw_form_line("Numéro de laboratoire", patient.prenoms)
    draw_form_line("Nom du centre", patient.prenoms)
    draw_form_line("Code du centre", patient.prenoms)
    draw_form_line("MI=Maladies Infect CHU Treichville", patient.prenoms)
    draw_form_line("CA = CAT Adjame", patient.prenoms)
    draw_form_line("PC = PPH CHU de Cocody", patient.prenoms)
    draw_form_line("PY = Pédiatrie CHU de Yopougon", patient.prenoms)
    draw_form_line("PB = Port-Bouët", patient.prenoms)
    draw_form_line("AG = Abengourou", patient.prenoms)
    draw_form_line("US = USAC", patient.prenoms)
    draw_form_line("HM = Hôpital Militaire d'Abidjan", patient.prenoms)
    draw_form_line("CI = CIBRA", patient.prenoms)
    draw_form_line("Nom du Patien", patient.prenoms)
    draw_form_line("Prénoms du Patien", patient.prenoms)
    draw_form_line("Sexe", patient.prenoms)
    draw_form_line("Date de naissance", patient.prenoms)
    draw_form_line("Niveau d'instruction du patient", patient.prenoms)
    draw_form_line("Situation matrimoniale du patient", patient.prenoms)
    draw_form_line("Nationalité", patient.prenoms)
    draw_form_line("Lieu de résidence habituel", patient.prenoms)
    draw_form_line("Nom du médecin", patient.prenoms)

    draw_form_line("antécédents medicaux 01", patient.prenoms)
    draw_form_line("", patient.prenoms)
    draw_form_line("", patient.prenoms)
    draw_form_line("", patient.prenoms)

    draw_form_line("le patient a t-il bénéficié d'une prophylaxie antiretrovirale ?", patient.prenoms)
    draw_form_line("type de prophylaxie antiretrovirale ?", patient.prenoms)
    draw_form_line("le patient a t-il été sous traitement antiretrovirale ?", patient.prenoms)
    draw_form_line("le patient se rappel t-il de son dernier régime antiretrovirale ?", patient.prenoms)
    draw_form_line("Derniers régimes antiretrovirale ?", patient.prenoms)
    draw_form_line("le patient est t-il sous traitement prophylactique au Cotrimoxazole ?", patient.prenoms)
    draw_form_line("Stade évolutif (CDC 1993)", patient.prenoms)
    draw_form_line("Le Patient a t-il une IO en cours ? ", patient.prenoms)
    draw_form_line("Est-il présentement sous traitement ?  ", patient.prenoms)
    draw_form_line("Poids du patient ce jour en KG  ", patient.prenoms)
    draw_form_line("Score de Karnofsky  ", patient.prenoms)

    # Ajouter les informations de l'enquête VIH si disponible
    if enquete_vih:
        draw_form_line("Prophylaxie antirétrovirale", "Oui" if enquete_vih.prophylaxie_antiretrovirale else "Non")
        draw_form_line("Type de prophylaxie", enquete_vih.prophylaxie_type)
        draw_form_line("Traitement antirétroviral", "Oui" if enquete_vih.traitement_antiretrovirale else "Non")
        draw_form_line("Type de traitement", enquete_vih.traitement_type)
        draw_form_line("Dernier régime antirétroviral", "Oui" if enquete_vih.dernier_regime_antiretrovirale else "Non")
        draw_form_line("Type du dernier régime", enquete_vih.dernier_regime_antiretrovirale_type)
        draw_form_line("Traitement prophylactique Cotrimoxazole",
                       "Oui" if enquete_vih.traitement_prophylactique_cotrimoxazole else "Non")
        draw_form_line("Évolutif CDC 1993", enquete_vih.evolutif_cdc_1993)
        draw_form_line("Sous traitement", "Oui" if enquete_vih.sous_traitement else "Non")
        draw_form_line("Score Karnofsky", enquete_vih.score_karnofsky)
        draw_form_line("Descriptif", enquete_vih.descriptif)

    c.showPage()
    c.save()

    buffer.seek(0)
    response.write(buffer.getvalue())
    buffer.close()

    return response


@login_required
def hospitalisation_send_create(request, consultations_id, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    consultations = get_object_or_404(Consultation, id=consultations_id)
    if request.method == 'POST':
        form = HospitalizationSendForm(request.POST)
        if form.is_valid():
            hospi = form.save(commit=False)
            hospi.patient = patient
            hospi.admission_date = date.today()
            hospi.created_by = request.user.employee

            # Ensure 'service' is correctly handled
            lit = form.cleaned_data['bed']
            hospi.bed = lit
            hospi.rom = lit.box.chambre

            consultations.hospitalised = 2
            consultations.save()

            lit.occuper = True
            lit.occupant = patient
            lit.save()

            # Set the correct activity (assuming the activity is Consultation)
            activite = ServiceSubActivity.objects.filter(service=consultations.services, nom='Hospitalisation').first()
            hospi.activite = activite

            hospi.save()
            message = f"🛏 Le Patient : {patient.nom} {patient.prenoms}.est admis en Hospitalisation le {hospi.admission_date},  Lit : {hospi.bed.nom} ({hospi.bed.box.chambre.unite.nom})."
            send_sms(get_employees_to_notify(), message)
            messages.success(request, 'Patient transféré en hospitalisation avec succès!')
            return redirect('hospitalisation')
        else:
            messages.error(request, 'Le formulaire est invalide. Veuillez vérifier les informations.')
    else:
        form = HospitalizationSendForm()

    context = {
        'form': form,
        'patient': patient,
    }
    return redirect('hospitalisation')


@login_required
def mark_consultation_as_hospitalised(request, consultation_id, patient_id):
    consultation = get_object_or_404(Consultation, pk=consultation_id)

    if request.method == 'POST':
        form = HospitalizationForm(request.POST)
        if form.is_valid():
            hospitalization = form.save(commit=False)
            hospitalization.consultation = consultation
            hospitalization.admission_date = date.today()
            hospitalization.patient_id = patient_id
            hospitalization.save()

            # Mark the consultation as hospitalized
            consultation.hospitalised = True
            consultation.requested_at = date.today()
            consultation.save()

            messages.success(request, 'La demande a été transmise avec succès!')
            return redirect('detail_consultation', pk=consultation.pk)
        else:
            messages.error(request, 'Il y a eu une erreur dans le formulaire.')
    else:
        form = HospitalizationForm()

    return redirect('detail_consultation', pk=consultation.pk)


@login_required
def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            return redirect('appointment_list')
    else:
        form = AppointmentForm(instance=appointment)
    return render(request, 'pages/appointments/appointment_form.html', {'form': form})


@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.delete()
        return redirect('appointment_list')
    return render(request, 'pages/appointments/appointment_confirm_delete.html', {'appointment': appointment})


@login_required
def create_symptome_and_update_consultation(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)

    if request.method == 'POST':
        form = SymptomesForm(request.POST)
        for i in range(len(request.POST.getlist('nom[]'))):
            symptome = Symptomes(
                nom=request.POST.getlist('nom[]')[i],
                date_debut=request.POST.getlist('date_debut[]')[i],
            )
            symptome.patient = consultation.patient
            symptome.save()
            consultation.symptomes.add(symptome)
            messages.success(request, 'Symptôme créé et consultation mise à jour avec succès!')

        # if form.is_valid():
        #     symptome = form.save(commit=False)
        #     symptome.patient = consultation.patient
        #     try:
        #         symptome.save()
        #         consultation.symptomes.add(symptome)
        #         consultation.save()
        #
        #         messages.success(request, 'Symptôme créé et consultation mise à jour avec succès!')
        #     except Exception as e:
        #         messages.error(request, f'Erreur lors de la création du symptôme: {e}')
        #     return redirect('detail_consultation', pk=consultation.id)
        # else:
        #     messages.error(request, 'Erreur lors de la validation du formulaire. Veuillez vérifier les champs.')
    else:
        messages.error(request, 'Erreur lors de la validation du formulaire. Veuillez vérifier les champs.')
        form = SymptomesForm()

    return redirect('detail_consultation', pk=consultation.id)


@login_required
def symptome_delete(request, symp, consultation_id):
    symptomes = get_object_or_404(Symptomes, id=symp)
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        symptomes.delete()
        messages.success(request, 'supprimer avec succès!')
        return redirect('detail_consultation', pk=consultation.id)
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def consultation_delete(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        consultation.delete()
        messages.success(request, 'supprimer avec succès!')
        return redirect('consultation_list')
    return redirect('consultation_list')


@login_required
def Antecedents_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = AntecedentsMedicauxForm(request.POST)
        if form.is_valid():
            antecedent = form.save(commit=False)
            antecedent.patient = consultation.patient
            antecedent.save()
            consultation.antecedentsMedicaux.add(antecedent)
            consultation.save()
            messages.success(request, 'Antécédent médical ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création de l\'antécédent médical.')
    else:
        form = AntecedentsMedicauxForm()
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def enquete_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)

    if request.method == 'POST':
        form = EnqueteVihForm(request.POST)
        if form.is_valid():
            enquete = form.save(commit=False)
            enquete.patient = consultation.patient
            enquete.consultation = consultation
            enquete.save()
            # Si le formulaire contient des ManyToMany fields, il faut les sauvegarder après le save initial
            form.save_m2m()

            messages.success(request, 'Enquête VIH créée avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création de l\'Enquête.')
    else:
        form = EnqueteVihForm()

    return redirect('detail_consultation', pk=consultation.id)


@login_required
def Allergies_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = AllergiesForm(request.POST)
        if form.is_valid():
            allergy = form.save(commit=False)
            allergy.patient = consultation.patient
            allergy.save()
            consultation.allergies.add(allergy)
            consultation.save()
            messages.success(request, 'Allergie ajoutée avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création de l\'allergie.')
    else:
        form = AllergiesForm()
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def Examens_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            examen = form.save(commit=False)
            examen.patients_requested = consultation.patient
            examen.consultation = consultation
            examen.save()
            consultation.examens = examen
            consultation.save()
            messages.success(request, 'Examen ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création de l\'examen.')
    else:
        form = ExamenForm()
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def Conseils_add(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = ConseilsForm(request.POST)
        if form.is_valid():
            conseil = form.save()
            consultation.commentaires.add(conseil)
            consultation.save()
            messages.success(request, 'Conseil ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de l\'ajout du conseil.')
    else:
        form = ConseilsForm()
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def Rendezvous_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rendezvous = form.save()
            consultation.rendezvous.add(rendezvous)
            consultation.save()
            messages.success(request, 'Rendez-vous ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création du rendez-vous.')
    else:
        form = RendezVousForm()
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def Protocoles_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = ProtocolesForm(request.POST)
        if form.is_valid():
            protocole = form.save()
            consultation.protocoles.add(protocole)
            consultation.save()
            messages.success(request, 'Protocole ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création du protocole.')
    else:
        form = ProtocolesForm()
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def Constantes_create(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = ConstantesForm(request.POST)
        if form.is_valid():
            constantes = form.save(commit=False)
            constantes.patient = patient
            constantes.created_by = request.user.employee  # Assurez-vous que l'utilisateur connecté est un employé
            messages.success(request, 'Constantes ajoutés avec succès!')
            constantes.save()
            return redirect('attente')  # Remplacez par l'URL de redirection appropriée
        else:
            messages.error(request, 'Erreur lors de l\'enregistrement des constantes')
    else:
        form = ConstantesForm()

    return render(request, 'pages/constantes/constntes_form.html', {'form': form, 'patient': patient})


@login_required
def patient_list_view(request):
    return render(request, 'pages/patient_list_view.html')


class PatientListView(LoginRequiredMixin, FilterView):
    model = Patient
    template_name = "pages/global_search.html"
    context_object_name = "patients"
    paginate_by = 10
    ordering = ['-id']
    filterset_class = PatientFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # patient_nbr = Patient.objects.all().count()
        context['resultfiltre'] = self.object_list.count()
        context['filter'] = self.get_filterset(self.filterset_class)

        return context


@login_required
def add_cas_contact(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        form = CasContactForm(request.POST)
        if form.is_valid():
            cas_contact = form.save(commit=False)
            cas_contact.patient = patient  # Associer le cas contact au patient
            cas_contact.save()
            messages.success(request, "Cas contact ajouté avec succès.")
            return JsonResponse({'success': True, 'message': 'Cas contact ajouté avec succès.'}, status=200)
        else:
            # Retourner les erreurs du formulaire au format JSON
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # Si la requête est GET, affichez le formulaire
    form = CasContactForm()
    return render(request, 'add_cas_contact.html', {'form': form, 'patient': patient})


# class PatientDetailView(LoginRequiredMixin, DetailView):
#     model = Patient
#     template_name = "pages/dossier_patient.html"
#     context_object_name = "patientsdetail"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         patient = self.get_object()
#         services_with_consultations = []
#
#         for service in patient.services_passed:
#             consultations = service.consultations.filter(patient=patient)
#             services_with_consultations.append((service, consultations))
#
#         context['services_with_consultations'] = services_with_consultations
#
#         # Récupérer les éléments liés au patient
#         context["consultations"] = patient.consultation_set.all().order_by('-created_at')
#         context["appointments"] = patient.appointments.all().order_by('-created_at')
#         context["suivis"] = patient.suivimedecin.all()
#         context['case_contacts'] = self.object.case_contacts.all()
#         context['cascontactsForm'] = CasContactForm()
#
#         # Ajouter les hospitalisations
#         hospitalizations = patient.hospitalized.all().prefetch_related(
#             'indicateurs_biologiques',
#             'indicateurs_fonctionnels',
#             'indicateurs_subjectifs',
#             'indicateurs_compliques',
#             'indicateurs_autres',
#         ).order_by('-created_at')
#
#         context['hospitalizations'] = hospitalizations
#
#         return context
class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = "pages/dossier_patient.html"
    context_object_name = "patientsdetail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object

        # -----------------------------
        # CONSULTATIONS (optimisées)
        # -----------------------------
        consultations = (
            Consultation.objects
            .filter(patient=patient)
            .select_related("doctor", "services", "suivi", "constante", "examens")
            .prefetch_related("symptomes", "antecedentsMedicaux", "allergies")
            .order_by("-consultation_date")
        )
        context["consultations"] = consultations

        # -----------------------------
        # RENDEZ-VOUS / SUIVIS
        # -----------------------------
        context["appointments"] = patient.appointments.all().order_by("-created_at")
        context["suivis"] = patient.suivimedecin.all()

        # -----------------------------
        # CAS CONTACTS
        # -----------------------------
        context["case_contacts"] = patient.case_contacts.all()
        context["cascontactsForm"] = CasContactForm()

        # -----------------------------
        # HOSPITALISATIONS FULL
        # -----------------------------
        hospitalizations = (
            Hospitalization.objects
            .filter(patient=patient)
            .select_related("doctor", "bed", "bed__box")
            .prefetch_related(
                "diagnostics",
                "hospiconstantes",
                "hospitalization_exams",
                "bilans",
                "imagerieshospi",
                "hospiantecedents",
                "hospimodedevie",
                "examens_appareils",
                "indicateurs_biologiques",
                "indicateurs_fonctionnels",
                "indicateurs_subjectifs",
                "indicateurs_compliques",
                "indicateurs_autres",
                Prefetch(
                    "hospiprescriptions",
                    queryset=Prescription.objects
                        .select_related("doctor", "medication", "created_by", "executed_by", "cancellation_by")
                        .prefetch_related("executions")
                        .order_by("-prescribed_at")
                ),
            )
            .order_by("-admission_date")
        )
        context["hospitalizations"] = hospitalizations

        # -----------------------------
        # PHARMACIE (toutes prescriptions du patient)
        # -----------------------------
        prescriptions = (
            Prescription.objects
            .filter(patient=patient)
            .select_related("doctor", "medication", "hospitalisation", "created_by", "executed_by", "cancellation_by")
            .prefetch_related("executions")
            .order_by("-prescribed_at")
        )
        context["prescriptions"] = prescriptions

        # -----------------------------
        # EXAMENS PARACLINIQUES (patient)
        # -----------------------------
        context["paraclinical_exams"] = (
            ParaclinicalExam.objects
            .filter(patient=patient)
            .select_related("hospitalisation")
            .order_by("-prescribed_at")
        )

        # -----------------------------
        # EXAMENS "DEMANDE LABO" (Examen lié aux consultations)
        # Ton modèle Examen a patients_requested + consultation
        # -----------------------------
        context["consultation_examens"] = (
            Examen.objects
            .filter(patients_requested=patient)
            .select_related("consultation", "analyses")
            .order_by("-created_at")
        )

        # -----------------------------
        # BILANS PARACLINIQUES
        # -----------------------------
        context["bilans"] = (
            BilanParaclinique.objects
            .filter(patient=patient)
            .select_related("doctor", "hospitalisation", "examen", "examen__type_examen")
            .order_by("-created_at")
        )

        # -----------------------------
        # IMAGERIE
        # -----------------------------
        context["imageries"] = (
            ImagerieMedicale.objects
            .filter(patient=patient)
            .select_related("hospitalisation", "type_imagerie", "medecin_prescripteur", "radiologue")
            .order_by("-date_examen")
        )

        # -----------------------------
        # CONSTANTES (patient global)
        # -----------------------------
        context["constantes"] = (
            Constante.objects
            .filter(patient=patient, hospitalisation__isnull=True)
            .select_related("created_by")
            .order_by("-created_at")
        )

        # -----------------------------
        # TESTS VIH
        # -----------------------------
        context["tests_vih"] = (
            TestRapideVIH.objects
            .filter(patient=patient)
            .select_related("consultation")
            .order_by("-date_test")
        )

        return context


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientCreateForm
    template_name = "pages/patient_create.html"
    success_url = reverse_lazy('global_search')  # Ensure 'global_search' points to your desired view

    def form_valid(self, form):
        # Normaliser les noms pour éviter les doublons à cause de la casse
        nom = form.cleaned_data['nom'].strip().upper()
        prenoms = form.cleaned_data['prenoms'].strip().upper()
        date_naissance = form.cleaned_data['date_naissance']
        contact = form.cleaned_data['contact'].strip()

        # Vérification des doublons (nom, prénoms, date de naissance)
        if Patient.objects.filter(
                nom__iexact=nom,
                prenoms__iexact=prenoms,
                date_naissance=date_naissance
        ).exists():
            messages.error(self.request, "Un patient avec les mêmes nom, prénoms et date de naissance existe déjà.")
            return self.form_invalid(form)

        # Vérification des doublons de contact
        if Patient.objects.filter(contact=contact).exists():
            messages.error(self.request, "Un patient avec ce contact existe déjà.")
            return self.form_invalid(form)

        # Création du patient
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user.employee

        # Gestion des informations de localité
        commune = form.cleaned_data.get('commune')
        if commune:
            self.object.localite = commune
            self.object.save()

        self.object.save()

        messages.success(self.request, "Patient créé avec succès !")
        return redirect(self.success_url)


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientUpdateForm
    template_name = "pages/patient_update.html"

    def get_success_url(self):
        return reverse_lazy('global_search')

    def form_valid(self, form):
        patient = form.instance
        nom = form.cleaned_data['nom'].upper()
        prenoms = form.cleaned_data['prenoms'].upper()
        date_naissance = form.cleaned_data.get('date_naissance')
        contact = form.cleaned_data['contact']

        # Vérification des doublons (autres patients sauf celui en cours de modification)
        if Patient.objects.exclude(pk=patient.pk).filter(
                nom__iexact=nom, prenoms__iexact=prenoms, date_naissance=date_naissance
        ).exists():
            messages.error(self.request,
                           "Un autre patient avec les mêmes nom, prénoms et date de naissance existe déjà.")
            return self.form_invalid(form)

        if Patient.objects.exclude(pk=patient.pk).filter(contact=contact).exists():
            messages.error(self.request, "Un autre patient avec ce contact existe déjà.")
            return self.form_invalid(form)

        # Mise à jour de la localité
        commune = form.cleaned_data.get('localite')
        if commune:
            location_instance, _ = Location.objects.get_or_create(name=commune)
            patient.localite = location_instance

        # Regénérer le QR Code si les données changent
        if 'nom' in form.changed_data or 'prenoms' in form.changed_data or 'contact' in form.changed_data:
            patient.generate_qr_code()

        messages.success(self.request, "Informations du patient mises à jour avec succès!")
        return super().form_valid(form)


@login_required
@permission_required('appointments.view_patient_name', raise_exception=True)
def get_patient_name(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        return JsonResponse({
            'full_name': f"{appointment.patient.nom} {appointment.patient.prenoms}"
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)


class RendezVousListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "pages/appointments/appointment_list.html"
    context_object_name = "rendezvous"
    paginate_by = 10
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        rdv = Appointment.objects.all().count()
        rdv_pending = Appointment.objects.filter(status='Scheduled').count()

        context['rdvnumber'] = rdv
        context['rdvpending'] = rdv_pending
        return context


class RendezVousDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = "pages/appointments/appointment_detail.html"
    context_object_name = "rendezvousdetails"
    paginate_by = 10
    ordering = ['-id']


class AppointmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Appointment
    template_name = "pages/appointments/appointment_confirm_delete.html"  # Fichier HTML de confirmation
    success_url = reverse_lazy("rendezvous")  # Redirection après suppression

    def get_queryset(self):
        return Appointment.objects.filter(created_by=self.request.user)


class RendezVousConsultationUpdateView(LoginRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentUpdateForm
    template_name = "pages/appointments/appointment_update.html"
    context_object_name = "rendezvousupdate"
    success_url = reverse_lazy('appointment_list')


@login_required
@permission_required('core.view_patient_name', raise_exception=True)
def get_patient_all_name(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
        return JsonResponse({'full_name': f"{patient.nom} {patient.prenoms}"})
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)


class SalleAttenteListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "pages/appointments/waitingrom.html"
    context_object_name = "attente"
    paginate_by = 10
    ordering = ['-time']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        appointments = Appointment.objects.filter(date=today, status='Scheduled').order_by('time')
        appointments_nbr = Appointment.objects.filter(date=today, status='Scheduled').count()

        # Récupérer la dernière constante pour chaque patient

        context['salleattente_nbr'] = appointments_nbr
        context['salleattente'] = appointments
        context['constanteform'] = ConstantesForm()
        context['ConsultationSendForm'] = ConsultationSendForm()

        return context


class PatientRecuListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "pages/appointments/patient_recu.html"
    context_object_name = "recu"
    paginate_by = 10
    ordering = ['-time']

    def get_queryset(self):
        today = now().date()
        current_time = now().time()
        # Rendez-vous passés (y compris aujourd'hui < heure courante)
        return Appointment.objects.filter(
            Q(date__lt=today, status='Completed') | Q(date=today, time__lt=current_time)
        ).order_by('-date', '-time')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['salleattente_nbr'] = self.get_queryset().count()
        ctx['salleattente'] = ctx['object_list']
        ctx['constanteform'] = ConstantesForm()
        ctx['ConsultationSendForm'] = ConsultationSendForm()
        qs = self.request.GET.copy()
        qs.pop('page', True)  # retire la page courante
        ctx['qs'] = qs.urlencode()  # ex: "status=Completed&doctor=12"
        return ctx


# class ServiceContentDetailView(LoginRequiredMixin, DetailView):
#     model = ServiceSubActivity
#     context_object_name = "subservice"
#
#     # ---------------------------------------------------
#     # TEMPLATE RESOLUTION
#     # ---------------------------------------------------
#     def get_template_names(self):
#
#         service = self.object.service
#         sub = self.object
#
#         service_slug = slugify(service.nom).upper()
#         activity_slug = slugify(sub.nom)
#
#         candidates = [
#             f"pages/services/{service_slug}/{activity_slug}.html",
#             f"pages/services/default/{activity_slug}.html",
#             "pages/services/servicecontent_detail.html",
#         ]
#
#         for tpl in candidates:
#             try:
#                 get_template(tpl)
#                 return [tpl]
#             except TemplateDoesNotExist:
#                 pass
#
#         return ["pages/services/servicecontent_detail.html"]
#
#     # ---------------------------------------------------
#     # CONTEXT
#     # ---------------------------------------------------
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         service = self.object.service
#         sub = self.object
#
#         context["service"] = service
#         context["subservice"] = sub
#
#         # ==================================================
#         #  Cas spécifique VIH-SIDA (overview uniquement)
#         # ==================================================
#         if service.nom == "VIH-SIDA" and sub.nom == "Overview":
#             self.build_vih_overview_context(context)
#
#         return context
#
#     # ---------------------------------------------------
#     #  VIH dashboard logic isolée
#     # ---------------------------------------------------
#     def build_vih_overview_context(self, context):
#
#         now = timezone.now()
#         date_debut = now - timedelta(days=365)
#
#         tests = TestRapideVIH.objects.filter(
#             consultation__services__nom="VIH-SIDA"
#         )
#
#         total_tests = tests.count()
#         total_positifs = tests.filter(resultat='POSITIF').count()
#
#         taux_positivite = round(
#             (total_positifs / total_tests) * 100, 2
#         ) if total_tests else 0
#
#         mois_labels = []
#         tests_data = []
#         positifs_data = []
#
#         current_month = now.month
#         last_month = (now - timedelta(days=30)).month
#
#         test_this_month = 0
#         test_last_month = 0
#         positif_this_month = 0
#         positif_last_month = 0
#
#         for i in range(12):
#             mois = now - timedelta(days=30 * (11 - i))
#             mois_labels.append(mois.strftime("%b %Y"))
#
#             mois_debut = mois.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#             mois_fin = (mois_debut + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
#
#             tests_mois = tests.filter(date_test__range=(mois_debut, mois_fin))
#
#             tests_count = tests_mois.count()
#             positifs_count = tests_mois.filter(resultat='POSITIF').count()
#
#             tests_data.append(tests_count)
#             positifs_data.append(positifs_count)
#
#             if mois.month == current_month:
#                 test_this_month = tests_count
#                 positif_this_month = positifs_count
#
#             elif mois.month == last_month:
#                 test_last_month = tests_count
#                 positif_last_month = positifs_count
#
#         def variation(new, old):
#             if old == 0:
#                 return 0
#             return round(((new - old) / old) * 100, 2)
#
#         test_change = variation(test_this_month, test_last_month)
#         positif_change = variation(positif_this_month, positif_last_month)
#
#         # ⚠️ attention : dans ton modèle Patient -> genre = 'HOMME' / 'FEMME'
#         hommes_tests = tests.filter(patient__genre='HOMME').count()
#         hommes_positifs = tests.filter(patient__genre='HOMME', resultat='POSITIF').count()
#
#         femmes_tests = tests.filter(patient__genre='FEMME').count()
#         femmes_positifs = tests.filter(patient__genre='FEMME', resultat='POSITIF').count()
#
#         hommes_taux = round((hommes_positifs / hommes_tests) * 100, 2) if hommes_tests else 0
#         femmes_taux = round((femmes_positifs / femmes_tests) * 100, 2) if femmes_tests else 0
#
#         traitements = TraitementARV.objects.filter(
#             type_traitement__in=[
#                 'première_ligne',
#                 'deuxième_ligne',
#                 'troisième_ligne'
#             ]
#         )
#
#         suivi_arv = Suivi.objects.filter(services__nom="VIH-SIDA")
#
#         context.update({
#
#             "total_tests": total_tests,
#             "total_positifs": total_positifs,
#             "taux_positivite": taux_positivite,
#
#             "test_change": abs(test_change),
#             "positif_change": abs(positif_change),
#
#             "test_change_sign": "↑" if test_change > 0 else "↓" if test_change < 0 else "=",
#             "positif_change_sign": "↑" if positif_change > 0 else "↓" if positif_change < 0 else "=",
#
#             "mois_labels": mois_labels,
#             "tests_data": tests_data,
#             "positifs_data": positifs_data,
#
#             "hommes_tests": hommes_tests,
#             "hommes_positifs": hommes_positifs,
#             "hommes_taux": hommes_taux,
#
#             "femmes_tests": femmes_tests,
#             "femmes_positifs": femmes_positifs,
#             "femmes_taux": femmes_taux,
#
#             "total_arv": traitements.count(),
#
#             "arv_adherence_bonne": suivi_arv.filter(adherence_traitement="bonne").count(),
#             "arv_adherence_moyenne": suivi_arv.filter(adherence_traitement="moyenne").count(),
#             "arv_adherence_faible": suivi_arv.filter(adherence_traitement="faible").count(),
#
#             "derniers_tests": tests.select_related("patient").order_by("-date_test")[:5],
#
#             "consultations_recentes": Consultation.objects.filter(
#                 services__nom="VIH-SIDA"
#             ).order_by("-consultation_date")[:5],
#
#             "prochains_rdv": Appointment.objects.filter(
#                 service__nom="VIH-SIDA",
#                 date__gte=now.date(),
#                 status="Scheduled"
#             ).order_by("date", "time")[:5],
#
#             "hospitalisations_vih": Hospitalization.objects.filter(
#                 activite__service__nom="VIH-SIDA",
#                 discharge_date__isnull=True
#             ).order_by("-admission_date")[:3],
#
#             "suivis_recents": suivi_arv.order_by("-date_suivi")[:3],
#
#             "mois_actuel": now.strftime("%B"),
#             "annee_actuelle": now.year,
#         })

class VIHFileActiveFilter(django_filters.FilterSet):
    code_vih = django_filters.CharFilter(
        field_name="vih_profile__code_vih",
        lookup_expr="icontains",
        label="Code VIH",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: AMI-0001"})
    )
    nom = django_filters.CharFilter(
        field_name="nom",
        lookup_expr="icontains",
        label="Nom",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"})
    )
    prenoms = django_filters.CharFilter(
        field_name="prenoms",
        lookup_expr="icontains",
        label="Prénoms",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénoms"})
    )
    contact = django_filters.CharFilter(
        field_name="contact",
        lookup_expr="icontains",
        label="Contact",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Téléphone"})
    )
    vih_status = django_filters.ChoiceFilter(
        field_name="vih_profile__status",
        choices=VIHProfile.VIHStatus.choices,
        label="Statut VIH",
        empty_label="Tous",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Patient
        fields = ["code_vih", "nom", "prenoms", "contact", "vih_status"]


class ServiceContentDetailView(LoginRequiredMixin, DetailView):
    model = ServiceSubActivity
    context_object_name = "subservice"

    # ---------------------------------------------------
    # TEMPLATE RESOLUTION (robuste nouveaux services)
    # ---------------------------------------------------
    def get_template_names(self):
        service = self.object.service
        sub = self.object

        service_slug = slugify(service.nom).upper()           # VIH-SIDA -> VIH-SIDA (ok si folder)
        activity_slug_dash = slugify(sub.nom)                 # File_active -> file-active
        activity_slug_underscore = activity_slug_dash.replace("-", "_")  # file_active

        candidates = [
            f"pages/services/{service_slug}/{activity_slug_dash}.html",
            f"pages/services/{service_slug}/{activity_slug_underscore}.html",
            f"pages/services/default/{activity_slug_dash}.html",
            f"pages/services/default/{activity_slug_underscore}.html",
            "pages/services/servicecontent_detail.html",
        ]

        for tpl in candidates:
            try:
                get_template(tpl)
                return [tpl]
            except TemplateDoesNotExist:
                continue

        return ["pages/services/servicecontent_detail.html"]

    # ---------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service = self.object.service
        sub = self.object

        context["service"] = service
        context["subservice"] = sub

        # Router VIH-SIDA
        if service.nom == "RETROVIRAUX":
            self.build_vih_context(context, sub.nom)

        return context

    # ---------------------------------------------------
    # VIH CONTEXT
    # ---------------------------------------------------
    def build_vih_context(self, context, sub_name: str):
        """
        Alimente les pages VIH:
        - Overview
        - File_active
        - Consultation
        - Hospitalisation
        - Suivi
        """

        now = timezone.now()

        # Base: patients VIH = ceux qui ont VIHProfile
        vih_patients = (
            Patient.objects
            .filter(vih_profile__status__in=["active", "transferred_in"])
            .select_related("vih_profile")  # pour patient.vih_profile sans N+1
            .order_by("-updated_at")
        )

        vih_patients_count = vih_patients.count()

        # --------------------------
        # FILE ACTIVE (liste patients VIH)
        # --------------------------
        if sub_name in ("File_active", "File active", "File-active"):
            base_qs = (
                Patient.objects
                .filter(vih_profile__isnull=False)
                .select_related("vih_profile")
                .order_by("-updated_at")
            )

            f = VIHFileActiveFilter(self.request.GET, queryset=base_qs)
            context["filter"] = f

            paginator = Paginator(f.qs, 10)  # ✅ on pagine la queryset filtrée
            page_number = self.request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context.update({
                "patients": page_obj.object_list,  # ✅ ton template boucle sur patients
                "page_obj": page_obj,  # ✅ ton template utilise page_obj
                "resultfiltre": paginator.count,  # ✅ nombre après filtre
                "patient_nbr": base_qs.count(),  # ✅ total VIH sans filtre
                "vih_patients_count": paginator.count,  # optionnel
            })
            return

        # --------------------------
        # CONSULTATIONS VIH
        # --------------------------
        if sub_name == "Consultation":
            consultations = (
                Consultation.objects
                .filter(services__nom="RETROVIRAUX")
                .select_related("doctor", "services", "suivi", "constante")
                .prefetch_related("symptomes", "antecedentsMedicaux", "allergies")
                .order_by("-consultation_date")
            )
            context["consultations"] = consultations
            context["consultations_count"] = consultations.count()
            return

        # --------------------------
        # HOSPITALISATIONS VIH
        # --------------------------
        if sub_name == "Hospitalisation":
            hospitalisations = (
                Hospitalization.objects
                .filter(activite__service__nom="RETROVIRAUX")
                .select_related("doctor", "bed", "bed__box", "activite", "activite__service")
                .order_by("-admission_date")
            )
            context["hospitalisations"] = hospitalisations
            context["hospitalisations_encours"] = hospitalisations.filter(discharge_date__isnull=True).count()
            context["hospitalisations_total"] = hospitalisations.count()
            return

        # --------------------------
        # SUIVI VIH
        # --------------------------
        if sub_name == "Suivi":
            suivis = (
                Suivi.objects
                .filter(services__nom="RETROVIRAUX")
                .select_related("patient", "services")
                .order_by("-date_suivi")
            )
            context["suivis"] = suivis
            context["suivis_count"] = suivis.count()
            return

        # --------------------------
        # OVERVIEW VIH (KPIs + graphes)
        # --------------------------
        if sub_name == "Overview":
            date_debut = now - timedelta(days=365)

            # Tests VIH sur 12 mois
            tests = (
                TestRapideVIH.objects
                .filter(date_test__gte=date_debut)
                # IMPORTANT : ne pas dépendre uniquement de consultation, certains tests peuvent être hors consultation
                .filter(patient__vih_profile__isnull=False)
                .select_related("patient", "consultation")
            )

            total_tests = tests.count()
            total_positifs = tests.filter(resultat="POSITIF").count()
            taux_positivite = round((total_positifs / total_tests) * 100, 2) if total_tests else 0

            # Evolution mensuelle (12 mois)
            mois_labels, tests_data, positifs_data = [], [], []
            current_month = now.month
            last_month = (now - timedelta(days=30)).month

            test_this_month = test_last_month = 0
            pos_this_month = pos_last_month = 0

            for i in range(12):
                mois = now - timedelta(days=30 * (11 - i))
                mois_labels.append(mois.strftime("%b %Y"))

                mois_debut = mois.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                mois_fin = (mois_debut + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

                tests_mois = tests.filter(date_test__range=(mois_debut, mois_fin))
                tcount = tests_mois.count()
                pcount = tests_mois.filter(resultat="POSITIF").count()

                tests_data.append(tcount)
                positifs_data.append(pcount)

                if mois.month == current_month:
                    test_this_month, pos_this_month = tcount, pcount
                elif mois.month == last_month:
                    test_last_month, pos_last_month = tcount, pcount

            def variation(new, old):
                if old == 0:
                    return 0
                return round(((new - old) / old) * 100, 2)

            test_change = variation(test_this_month, test_last_month)
            positif_change = variation(pos_this_month, pos_last_month)

            # Répartition sexe (attention à tes valeurs: HOMME/FEMME)
            hommes_tests = tests.filter(patient__genre="HOMME").count()
            hommes_positifs = tests.filter(patient__genre="HOMME", resultat="POSITIF").count()
            femmes_tests = tests.filter(patient__genre="FEMME").count()
            femmes_positifs = tests.filter(patient__genre="FEMME", resultat="POSITIF").count()

            hommes_taux = round((hommes_positifs / hommes_tests) * 100, 2) if hommes_tests else 0
            femmes_taux = round((femmes_positifs / femmes_tests) * 100, 2) if femmes_tests else 0

            # Activité clinique VIH
            consultations_recentes = (
                Consultation.objects
                .filter(services__nom="RETROVIRAUX")
                .order_by("-consultation_date")[:5]
            )

            hospitalisations_vih = (
                Hospitalization.objects
                .filter(activite__service__nom="RETROVIRAUX", discharge_date__isnull=True)
                .order_by("-admission_date")[:5]
            )

            suivis_recents = (
                Suivi.objects
                .filter(services__nom="RETROVIRAUX")
                .order_by("-date_suivi")[:5]
            )

            # File active
            vih_actifs = Patient.objects.filter(vih_profile__status="active").count()

            context.update({
                "vih_actifs": vih_actifs,

                "total_tests": total_tests,
                "total_positifs": total_positifs,
                "taux_positivite": taux_positivite,

                "test_change": abs(test_change),
                "positif_change": abs(positif_change),
                "test_change_sign": "↑" if test_change > 0 else "↓" if test_change < 0 else "=",
                "positif_change_sign": "↑" if positif_change > 0 else "↓" if positif_change < 0 else "=",

                "mois_labels": mois_labels,
                "tests_data": tests_data,
                "positifs_data": positifs_data,

                "hommes_tests": hommes_tests,
                "hommes_positifs": hommes_positifs,
                "hommes_taux": hommes_taux,

                "femmes_tests": femmes_tests,
                "femmes_positifs": femmes_positifs,
                "femmes_taux": femmes_taux,

                "derniers_tests": tests.order_by("-date_test")[:5],
                "consultations_recentes": consultations_recentes,
                "hospitalisations_vih": hospitalisations_vih,
                "suivis_recents": suivis_recents,

                "mois_actuel": now.strftime("%B"),
                "annee_actuelle": now.year,
            })
            return


class ActiviteListView(LoginRequiredMixin, ListView):
    context_object_name = 'activities'
    ordering = ['-created_at']
    paginate_by = 10

    def get_queryset(self):
        serv = self.kwargs['serv']
        acty = self.kwargs['acty']
        return ServiceSubActivity.objects.filter(service__nom=serv, nom=acty)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        serv = self.kwargs['serv']
        acty = self.kwargs['acty']
        acty_id = self.kwargs['acty_id']

        subactivity = ServiceSubActivity.objects.filter(service__nom=serv, nom=acty, id=acty_id).first()
        consultations = Consultation.objects.filter(activite=subactivity) if subactivity else []
        consultations_paginator = Paginator(consultations, 10)
        consultations_page = self.request.GET.get('consultations_page')
        context['consultations'] = consultations_paginator.get_page(consultations_page)

        hospitalizations = Hospitalization.objects.filter(activite=subactivity).order_by('-admission_date') if subactivity else []
        hospitalizations_paginator = Paginator(hospitalizations, 10)
        hospitalizations_page = self.request.GET.get('hospitalizations_page')
        context['hospitalizations'] = hospitalizations_paginator.get_page(hospitalizations_page)

        suivis = Suivi.objects.filter(services=subactivity.service) if subactivity else []  # Assuming you have a Suivi model
        suivis_paginator = Paginator(suivis, 10)
        suivis_page = self.request.GET.get('suivis_page')
        context['suivis'] = suivis_paginator.get_page(suivis_page)

        context.update({
            'serv': serv,
            'acty': acty,
            'acty_id': acty_id,
            'subactivity': subactivity,
            # 'consultations': consultations,
            # 'hospitalizations': hospitalizations,
            # 'suivis': suivis,
        })
        return context

    def get_template_names(self):
        serv = self.kwargs.get("serv") or ""
        acty = self.kwargs.get("acty") or ""

        # normaliser le nom de sous-activité => fichiers stables
        allowed = {
            "Overview": "overview",
            "File_active": "file_active",
            "Consultation": "consultation",
            "Hospitalisation": "hospitalisation",
            "Suivi": "suivi",
        }
        acty_key = allowed.get(acty, "overview")

        # normaliser le nom service => éviter espaces/accents etc.
        # (idéalement: utiliser un slug en DB, mais ici on fait simple)
        service_folder = serv.strip().replace(" ", "_")

        candidates = [
            f"pages/services/{service_folder}/{acty_key}.html",     # template dédié au service
            f"pages/services/default/{acty_key}.html",             # fallback générique
            "pages/services/servicecontent_detail.html",           # fallback ultime
        ]

        # retourne la première qui existe réellement
        for tpl in candidates:
            try:
                get_template(tpl)
                return [tpl]
            except TemplateDoesNotExist:
                continue

        return ["pages/services/servicecontent_detail.html"]


class VIHAccessMixin(UserPassesTestMixin):
    allowed_groups = ["VIH Team", "SMIT", "Admin VIH"]

    def test_func(self):
        u = self.request.user
        return (
            u.is_superuser
            or u.groups.filter(name__in=self.allowed_groups).exists()
        )

class VIHProfileDetailView(LoginRequiredMixin, VIHAccessMixin, DetailView):
    model = VIHProfile
    context_object_name = "vih_profile"
    template_name = "pages/services/RETROVIRAUX/vih_profile_detail.html"

    def get_object(self, queryset=None):
        return get_object_or_404(
            VIHProfile.objects.select_related("patient", "created_by", "updated_by"),
            pk=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vih = self.object
        patient = vih.patient
        today = timezone.now().date()

        # ---------------------------
        # Derniers suivis utiles
        # ---------------------------
        last_suivi = vih.last_suivi

        last_cd4 = getattr(last_suivi, "cd4", None) if last_suivi else None
        last_cv = getattr(last_suivi, "charge_virale", None) if last_suivi else None
        last_poids = getattr(last_suivi, "poids", None) if last_suivi else None

        # si tu stockes stage OMS dans "oms_stage" du suivi, ok,
        # sinon fallback sur vih.oms_stage
        last_stade = getattr(last_suivi, "oms_stage", None) if last_suivi else None
        if not last_stade:
            last_stade = getattr(vih, "oms_stage", None)

        # ---------------------------
        # QuerySets
        # ---------------------------
        suivis_qs = vih.suivis
        arv_qs = vih.traitements_arv
        exams_qs = vih.exams_bilan
        depistages_qs = vih.depistages_vih
        io_qs = vih.infections_opportunistes
        comorb_qs = vih.comorbidites

        # ---------------------------
        # Counts
        # ---------------------------
        counts = {
            "suivis": suivis_qs.count(),
            "arv": arv_qs.count(),
            "exams": exams_qs.count(),
            "depistages": depistages_qs.count(),
            "io": io_qs.count(),
            "comorbidites": comorb_qs.count(),
        }

        # ---------------------------
        # Listes (limitées)
        # ---------------------------
        exams_list = list(exams_qs[:50])
        depistages_list = list(depistages_qs[:50])
        io_list = list(io_qs[:50])
        comorb_list = list(comorb_qs[:50])

        # ---------------------------
        # Prescriptions ARV (optionnel)
        # ---------------------------
        arv_prescriptions = []
        if hasattr(patient, "prescriptions"):
            arv_prescriptions = list(
                patient.prescriptions.select_related("medication").order_by("-prescribed_at")[:10]
            )

        # ---------------------------
        # Timeline unifiée (safe)
        # ---------------------------
        timeline = []

        for s in suivis_qs:
            timeline.append({
                "type": "suivi",
                "date": getattr(s, "date_suivi", None) or getattr(s, "created_at", None),
                "title": "Consultation / suivi",
                "meta": f"CD4: {s.cd4}" if getattr(s, "cd4", None) else None,
            })

        for a in arv_qs:
            title = "Traitement ARV"
            meta = getattr(a, "regimen", None) or getattr(a, "regimen_code", None) or None
            timeline.append({
                "type": "arv",
                "date": getattr(a, "date_mise_a_jour", None) or getattr(a, "date_creation", None),
                "title": title,
                "meta": meta,
            })

        for e in exams_qs:
            exam_date = e.performed_at or e.prescribed_at or e.created_at

            result_short = None
            if e.result_value is not None:
                result_short = str(e.result_value)
            elif e.result_text:
                result_short = (e.result_text[:50] + "…") if len(e.result_text) > 50 else e.result_text

            meta_parts = []
            meta_parts.append(e.exam_type)  # obligatoire
            meta_parts.append(f"#{e.iteration}" if e.iteration else None)
            meta_parts.append(e.get_status_display())
            if result_short:
                meta_parts.append(f"Résultat: {result_short}")

            meta_parts = [m for m in meta_parts if m]

            timeline.append({
                "type": "exam",
                "date": exam_date,
                "title": e.exam_name or "Examen paraclinique",
                "meta": " • ".join(meta_parts) if meta_parts else None,
            })

        for d in depistages_qs:
            meta = None
            if hasattr(d, "get_resultat_display"):
                meta = d.get_resultat_display()
            else:
                meta = getattr(d, "resultat", None)

            timeline.append({
                "type": "depistage",
                "date": getattr(d, "date_test", None) or getattr(d, "created_at", None),
                "title": "Dépistage VIH",
                "meta": meta,
            })

        for io in io_qs:
            timeline.append({
                "type": "io",
                "date": getattr(io, "date_diagnostic", None) or getattr(io, "date_creation", None),
                "title": "Infection opportuniste",
                "meta": str(getattr(io, "type_infection", "")) or None,
            })

        for c in comorb_qs:
            timeline.append({
                "type": "comorb",
                "date": getattr(c, "date_diagnostic", None) or getattr(c, "date_creation", None),
                "title": "Comorbidité",
                "meta": str(getattr(c, "type_comorbidite", "")) or None,
            })

        timeline_events = sorted(
            timeline,
            key=lambda x: x["date"] or timezone.now(),
            reverse=True
        )

        # ---------------------------
        # Visites
        # ---------------------------
        days_since_last = None
        if vih.date_derniere_visite:
            days_since_last = (today - vih.date_derniere_visite).days

        days_until_next = None
        is_next_overdue = False
        is_next_soon = False
        if vih.date_prochaine_visite:
            days_until_next = (vih.date_prochaine_visite - today).days
            is_next_overdue = days_until_next < 0
            is_next_soon = 0 <= days_until_next <= 7

        # ---------------------------
        # ARV depuis
        # ---------------------------
        arv_days = None
        if vih.date_debut_arv:
            arv_days = (today - vih.date_debut_arv).days

        context.update({
            "counts": counts,

            "last_suivi": last_suivi,
            "last_cd4": last_cd4,
            "last_cv": last_cv,
            "last_poids": last_poids,
            "last_stade": last_stade,

            "exams_list": exams_list,
            "depistages_list": depistages_list,
            "io_list": io_list,
            "comorb_list": comorb_list,

            "timeline_events": timeline_events,

            "days_since_last_visit": days_since_last,
            "days_until_next_visit": days_until_next,
            "is_next_visit_overdue": is_next_overdue,
            "is_next_visit_soon": is_next_soon,

            "arv_days": arv_days,
            "arv_prescriptions": arv_prescriptions,
        })

        return context
class ConstanteUpdateView(LoginRequiredMixin, UpdateView):
    model = Constante
    form_class = ConstantesForm
    template_name = "pages/constantes/constntes_form.html"
    success_url = reverse_lazy('attente')


class ConsultationListView(LoginRequiredMixin, ListView):
    model = Consultation
    template_name = 'consultations/consultation_list.html'  # Chemin vers votre template
    context_object_name = 'consultations'
    ordering = ['-consultation_date']
    paginate_by = 10


@login_required
def test_rapide_consultation_generale_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = TestRapideVIHForm(request.POST)
        if form.is_valid():
            test_rapide = form.save(commit=False)
            test_rapide.patient = consultation.patient
            test_rapide.consultation = consultation
            test_rapide.test_type = form.cleaned_data['test_type']
            test_rapide.commentaire = form.cleaned_data['commentaire']

            test_rapide.save()
            messages.success(request, 'Rendez-vous ajouté avec succès!')
            return redirect('consultation_detail', pk=consultation.id)
    else:
        form = TestRapideVIHForm()
        messages.error(request, 'Le test a echoué!')
    return redirect('consultation_detail', pk=consultation.id)


@login_required
def delete_test_rapide_consultation_generale(request, test_id, consultation_id):
    # Récupérer l'objet TestRapideVIH avec l'id fourni
    test_rapide = get_object_or_404(TestRapideVIH, id=test_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Vérifie que la requête est bien une requête POST (pour éviter les suppressions accidentelles)

    test_rapide.delete()
    messages.success(request, 'Le test rapide VIH a été supprimé avec succès.')
    # Redirection après suppression (à personnaliser selon vos besoins)
    return redirect('consultation_detail', pk=consultation.id)


@login_required
def Examens_Consultation_generale_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            examen = form.save(commit=False)
            examen.patients_requested = consultation.patient
            examen.consultation = consultation
            examen.save()
            consultation.examens = examen
            consultation.save()
            messages.success(request, 'Examen ajouté avec succès!')
            return redirect('consultation_detail', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création de l\'examen.')
    else:
        form = ExamenForm()
    return redirect('consultation_detail', pk=consultation.id)


class ConsultationDetailView(LoginRequiredMixin, DetailView):
    model = Consultation
    template_name = 'consultations/consultation_detail.html'
    context_object_name = 'consultationsdupatient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        consultation = self.object  # 🔑 la consultation actuelle

        # ✅ Vérifier s'il y a déjà un échantillon pour sérologie VIH
        serologie_vih_exist = Echantillon.objects.filter(
            consultation=consultation,
            patient=consultation.patient,
            # examen_demande__nom__icontains="VIH"
        ).exists()

        context['serologie_vih_exist'] = serologie_vih_exist

        # ✅ Tout ton contexte habituel
        context['formconsult'] = ConsultationCreateForm()
        context['examen_form'] = ExamenForm()
        context['prescription_form'] = PrescriptionForm()
        context['antecedentsMedicaux_form'] = AntecedentsMedicauxForm()
        context['allergies_form'] = AllergiesForm()
        context['conseils_form'] = ConseilsForm()
        context['hospit_form'] = HospitalizationSendForm()
        context['hospit_request'] = HospitalizationForm()
        context['depistage_form'] = TestRapideVIHForm()
        context['prelevement_form'] = EchantillonForm()
        context['suivisform'] = SuiviSendForm()
        context['symptomes_form'] = SymptomesForm()
        context['symptomes_forms'] = [SymptomesForm(prefix=str(i)) for i in range(1)]

        return context


class ConsultationUpdateView(LoginRequiredMixin, UpdateView):
    model = Consultation
    form_class = ConsultationForm
    template_name = 'consultations/consultation_form.html'

    def get_success_url(self):
        return reverse_lazy('consultation_detail', kwargs={'pk': self.object.pk})


class ConsultationDeleteView(LoginRequiredMixin, DeleteView):
    model = Consultation
    template_name = 'consultations/consultation_confirm_delete.html'
    success_url = reverse_lazy('consultation_list')


class ConsultationSidaListView(LoginRequiredMixin, ListView):
    model = Consultation
    template_name = "pages/services/consultation_VIH.html"
    context_object_name = "consultations_vih"


@login_required
def test_rapide_vih_create(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if request.method == 'POST':
        form = TestRapideVIHForm(request.POST)
        if form.is_valid():
            test_rapide = form.save(commit=False)
            test_rapide.patient = consultation.patient
            test_rapide.consultation = consultation
            test_rapide.test_type = form.cleaned_data['test_type']
            test_rapide.commentaire = form.cleaned_data['commentaire']

            test_rapide.save()
            messages.success(request, 'Rendez-vous ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
    else:
        form = TestRapideVIHForm()
        messages.error(request, 'Le test a echoué!')
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def delete_test_rapide_vih(request, test_id, consultation_id):
    # Récupérer l'objet TestRapideVIH avec l'id fourni
    test_rapide = get_object_or_404(TestRapideVIH, id=test_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Vérifie que la requête est bien une requête POST (pour éviter les suppressions accidentelles)

    test_rapide.delete()
    messages.success(request, 'Le test rapide VIH a été supprimé avec succès.')
    # Redirection après suppression (à personnaliser selon vos besoins)
    return redirect('detail_consultation', pk=consultation.id)


@login_required
def delete_examen(request, examen_id, consultation_id):
    # Récupérer l'objet TestRapideVIH avec l'id fourni
    examen = get_object_or_404(Examen, id=examen_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Vérifie que la requête est bien une requête POST (pour éviter les suppressions accidentelles)

    examen.delete()
    messages.success(request, 'L\'examen a été supprimé avec succès.')
    # Redirection après suppression (à personnaliser selon vos besoins)
    return redirect('detail_consultation', pk=consultation.id)


# def test_rapide_vih_update(request, pk):
#     test = get_object_or_404(TestRapideVIH, pk=pk)
#     if request.method == 'POST':
#         form = TestRapideVIHForm(request.POST, instance=test)
#         if form.is_valid():
#             form.save()
#             return redirect('test_rapide_vih_list')
#     else:
#         form = TestRapideVIHForm(instance=test)
#     return render(request, 'test_rapide_vih_form.html', {'form': form})
@login_required
def create_recurrent_appointments(rdv):
    """Génère des rendez-vous récurrents basés sur les paramètres de récurrence"""
    current_date = rdv.date
    end_date = rdv.recurrence_end_date

    # Déterminer l'intervalle de récurrence
    if rdv.recurrence == 'Weekly':
        interval = timedelta(weeks=1)
    elif rdv.recurrence == 'Monthly':
        interval = timedelta(weeks=4)
    elif rdv.recurrence == 'Quarterly':
        interval = timedelta(weeks=12)
    elif rdv.recurrence == 'Semi-Annual':
        interval = timedelta(weeks=26)
    elif rdv.recurrence == 'Annual':
        interval = timedelta(weeks=52)
    else:
        return  # Pas de récurrence

    # Générer les rendez-vous jusqu'à la date de fin de récurrence
    while current_date < end_date:
        current_date += interval
        RendezVous.objects.create(
            patient=rdv.patient,
            service=rdv.service,
            doctor=rdv.doctor,
            calendar=rdv.calendar,
            event=rdv.event,
            date=current_date,
            time=rdv.time,
            reason=rdv.reason,
            status='Scheduled',
            created_by=rdv.created_by,
            recurrence='None'  # Pas de récurrence pour les rendez-vous générés automatiquement
        )


class ConsultationSidaDetailView(LoginRequiredMixin, DetailView):
    model = Consultation
    template_name = "pages/services/VIH-SIDA/details_consultation_VIH.html"
    context_object_name = "consultationsdupatient"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['service'] = self.object.service  # Ajoutez le service parent au contexte
        context['formconsult'] = ConsultationCreateForm()  # Ajoutez le service parent au contexte
        context['examen_form'] = ExamenForm()
        context['prescription_form'] = PrescriptionForm()
        context['antecedentsMedicaux_form'] = AntecedentsMedicauxForm()
        context['allergies_form'] = AllergiesForm()
        context['conseils_form'] = ConseilsForm()
        context['EnqueteVihForm'] = EnqueteVihForm()
        context['hospit_form'] = HospitalizationSendForm()
        context['hospit_request'] = HospitalizationForm()
        context['depistage_form'] = TestRapideVIHForm()
        context['prelevement_form'] = EchantillonForm()
        context['suivisform'] = SuiviSendForm()

        context['symptomes_form'] = SymptomesForm()
        context['symptomes_forms'] = [SymptomesForm(prefix=str(i)) for i in range(1)]
        return context


@login_required
def suivi_send_create(request, consultationsvih_id, patient_id):
    # Récupérer le patient et la consultation
    patient = get_object_or_404(Patient, id=patient_id)
    consultation = get_object_or_404(Consultation, id=consultationsvih_id)

    if request.method == 'GET':  # Action déclenchée via un simple clic
        try:
            # Vérifier si un suivi existe déjà pour ce patient et cette consultation
            suivi_existe = Suivi.objects.filter(
                patient=patient,
                activite=consultation.activite,
                services=consultation.services,
                # date_suivi=now().date()  # Vérifie un suivi créé aujourd'hui
            ).exists()

            if suivi_existe:
                # Si un suivi existe déjà, afficher un message d'erreur
                messages.error(request,
                               f"Un suivi existe déjà pour le patient {patient.nom} pour cette activité et ce service.")
                return redirect('suivi_list')

            # Créer une nouvelle instance de suivi
            suivi = Suivi.objects.create(
                patient=patient,
                activite=consultation.activite,  # Activité associée
                services=consultation.services,  # Service associé
                date_suivi=now().date(),  # Date de suivi (par défaut aujourd'hui)
                poids=patient.latest_poids if hasattr(patient, 'latest_poids') else None,  # Poids, si disponible
                observations=f"Suivi créé pour la consultation {consultation.numeros}.",
                statut_patient='actif',  # Statut par défaut
                adherence_traitement='bonne',  # Adhérence par défaut
            )

            # Mettre à jour la consultation (optionnel)
            consultation.status = 'Completed'
            consultation.save()

            # Afficher un message de succès
            messages.success(request, f"Suivi créé avec succès pour le patient {patient.nom}.")
            return redirect('suivi_list')  # Rediriger vers la page de la liste des suivis

        except Exception as e:
            # Gérer les erreurs potentielles
            messages.error(request, f"Une erreur s'est produite lors de la création du suivi : {e}")
            return redirect('suivi_list')

    # Si la méthode HTTP est incorrecte
    messages.error(request, "Action non autorisée.")
    return redirect('suivi_list')


@login_required
def suivi_send_from_bilan(request, consultation_id, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)
    # Récupérer le bilan initial associé à cette consultation s'il existe
    bilaninitial = BilanInitial.objects.filter(
        consultation=consultation_id,
        # Si tu as un lien explicite entre Consultation et BilanInitial, utilise-le
        # ex: bilaninitial = get_object_or_404(BilanInitial, consultation=consultation)
    ).first()

    if request.method == 'GET':  # Action déclenchée via un simple clic
        try:
            # Vérifier si un suivi existe déjà pour ce patient et cette consultation
            suivi_existe = Suivi.objects.filter(
                patient=patient,
                activite=consultation.activite,
                services=consultation.services,
                # date_suivi=now().date()  # Vérifie un suivi créé aujourd'hui
            ).exists()

            if suivi_existe:
                # Si un suivi existe déjà, afficher un message d'erreur
                messages.error(request,
                               f"Un suivi existe déjà pour le patient {patient.nom} pour cette activité et ce service.")
                return redirect('suivi_list')

            # Créer une nouvelle instance de suivi
            suivi = Suivi.objects.create(
                patient=patient,
                activite=consultation.activite,  # Activité associée
                services=consultation.services,  # Service associé
                date_suivi=now().date(),  # Date de suivi (par défaut aujourd'hui)
                poids=patient.latest_poids if hasattr(patient, 'latest_poids') else None,  # Poids, si disponible
                observations=f"Suivi créé pour la consultation {consultation.numeros}.",
                statut_patient='actif',  # Statut par défaut
                adherence_traitement='bonne',  # Adhérence par défaut
            )

            # Mettre à jour la consultation (optionnel)
            consultation.status = 'Completed'
            consultation.save()

            # Mettre à jour le statut du bilan initial si trouvé
            if bilaninitial:
                bilaninitial.status = 'suivi'
                bilaninitial.save()

            # Afficher un message de succès
            messages.success(request, f"Suivi créé avec succès pour le patient {patient.nom}.")
            return redirect('suivi_list')  # Rediriger vers la page de la liste des suivis

        except Exception as e:
            # Gérer les erreurs potentielles
            messages.error(request, f"Une erreur s'est produite lors de la création du suivi : {e}")
            return redirect('suivi_list')

    # Si la méthode HTTP est incorrecte
    messages.error(request, "Action non autorisée.")
    return redirect('suivi_list')


class SuiviListView(LoginRequiredMixin, ListView):
    model = Suivi
    template_name = "pages/suivi/suivi_list.html"
    context_object_name = "suivis"
    ordering = '-created_at'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Périodes de comparaison
        aujourdhui = timezone.now().date()
        mois_dernier = aujourdhui - timedelta(days=30)
        semaine_derniere = aujourdhui - timedelta(days=7)

        # Patients actifs
        patients_actifs = Suivi.objects.filter(statut_patient='actif').count()
        patients_actifs_mois_dernier = Suivi.objects.filter(
            statut_patient='actif',
            date_suivi__month=mois_dernier.month,
            date_suivi__year=mois_dernier.year
        ).count()

        # Patients perdus de vue
        patients_perdus_vue = Suivi.objects.filter(statut_patient='perdu_de_vue').count()
        patients_perdus_mois_dernier = Suivi.objects.filter(
            statut_patient='perdu_de_vue',
            date_suivi__month=mois_dernier.month,
            date_suivi__year=mois_dernier.year
        ).count()

        # Taux d'adhérence
        suivi_adherence = Suivi.objects.exclude(adherence_traitement='')
        taux_adherence = suivi_adherence.filter(
            adherence_traitement='bonne').count() / suivi_adherence.count() * 100 if suivi_adherence.count() > 0 else 0
        taux_adherence_mois_dernier = Suivi.objects.filter(
            date_suivi__month=mois_dernier.month,
            date_suivi__year=mois_dernier.year,
            adherence_traitement='bonne'
        ).count() / Suivi.objects.filter(
            date_suivi__month=mois_dernier.month,
            date_suivi__year=mois_dernier.year
        ).exclude(adherence_traitement='').count() * 100 if Suivi.objects.filter(
            date_suivi__month=mois_dernier.month,
            date_suivi__year=mois_dernier.year
        ).exclude(adherence_traitement='').count() > 0 else 0

        # Nouveaux patients (7 derniers jours)
        nouveaux_7j = Patient.objects.filter(
            created_at__gte=semaine_derniere
        ).count()
        nouveaux_7j_precedent = Patient.objects.filter(
            created_at__gte=semaine_derniere - timedelta(days=7),
            created_at__lt=semaine_derniere
        ).count()

        # Calcul des évolutions
        evolution_actifs = ((
                                    patients_actifs - patients_actifs_mois_dernier) / patients_actifs_mois_dernier * 100) if patients_actifs_mois_dernier > 0 else 0
        evolution_perdus = ((
                                    patients_perdus_vue - patients_perdus_mois_dernier) / patients_perdus_mois_dernier * 100) if patients_perdus_mois_dernier > 0 else 0
        evolution_adherence = ((
                                       taux_adherence - taux_adherence_mois_dernier) / taux_adherence_mois_dernier * 100) if taux_adherence_mois_dernier > 0 else 0
        evolution_nouveaux = ((
                                      nouveaux_7j - nouveaux_7j_precedent) / nouveaux_7j_precedent * 100) if nouveaux_7j_precedent > 0 else 0

        # Tendance sur 7 jours (simplifié - en production, utilisez des données réelles)
        jours_tendance = [(aujourdhui - timedelta(days=i)).strftime('%a %d/%m') for i in reversed(range(7))]

        tendance_actifs = [patients_actifs - i for i in range(7)]
        tendance_perdus = [patients_perdus_vue - i for i in range(7)]
        tendance_adherence = [int(taux_adherence) - i for i in range(7)]
        tendance_nouveaux = [nouveaux_7j - i for i in range(7)]

        context['stats'] = {
            'patients_actifs': patients_actifs,
            'evolution_actifs': evolution_actifs,
            # 'tendance_actifs': tendance_actifs[::-1],
            'tendance_actifs': json.dumps(tendance_actifs[::-1]),

            'patients_perdus_vue': patients_perdus_vue,
            'evolution_perdus': evolution_perdus,
            'tendance_perdus': tendance_perdus[::-1],

            'taux_adherence': round(taux_adherence, 1),
            'evolution_adherence': round(evolution_adherence, 1),
            'tendance_adherence': tendance_adherence[::-1],

            'nouveaux_7j': nouveaux_7j,
            'evolution_nouveaux': round(evolution_nouveaux, 1),
            'tendance_nouveaux': tendance_nouveaux[::-1],
            'jours_tendance': jours_tendance,
        }

        return context


def create_rdv(request, suivi_id):
    # Récupérer le suivi correspondant
    suivi = get_object_or_404(Suivi, id=suivi_id)

    if request.method == 'POST':
        form = RdvSuiviForm(request.POST, user=request.user)
        if form.is_valid():
            # Créer le rendez-vous sans l'enregistrer pour ajouter des données supplémentaires
            rdv = form.save(commit=False)
            rdv.suivi = suivi  # Associer le rendez-vous au suivi
            rdv.patient = suivi.patient  # Associer automatiquement le patient du suivi
            rdv.created_by = request.user.employee  # Associer le créateur
            rdv.save()
            messages.success(request, "Le rendez-vous a été créé avec succès.")
            return redirect('suivi-detail', pk=suivi.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = RdvSuiviForm()

    return render(request, 'pages/suivi/create_rdv.html', {
        'form': form,
        'suivi': suivi,
    })


def get_clinical_history(request, patient_id):
    # Récupère l'historique clinique pour les graphiques
    suivis = Suivi.objects.filter(patient_id=patient_id).exclude(date_suivi__isnull=True).order_by('date_suivi')

    # Données pour CD4
    cd4_data = {
        'dates': [s.date_suivi.strftime("%Y-%m-%d") for s in suivis if s.cd4],
        'values': [s.cd4 for s in suivis if s.cd4]
    }

    # Données pour poids
    weight_data = {
        'dates': [s.date_suivi.strftime("%Y-%m-%d") for s in suivis if s.poids],
        'values': [float(s.poids) for s in suivis if s.poids]
    }

    # Données pour charge virale
    viral_load_data = {
        'dates': [s.date_suivi.strftime("%Y-%m-%d") for s in suivis if s.charge_virale],
        'values': [s.charge_virale for s in suivis if s.charge_virale]
    }

    return JsonResponse({
        'cd4': cd4_data,
        'weight': weight_data,
        'viral_load': viral_load_data
    })


# def add_recommandation(request, suivi_id):
#     if request.method == 'POST':
#         suivi = get_object_or_404(Suivi, pk=suivi_id)
#         text = request.POST.get('recommandation')
#         if text:
#             Recommandation.objects.create(suivi=suivi, text=text, created_by=request.user)
#             messages.success(request, "Recommandation ajoutée avec succès")
#         else:
#             messages.error(request, "Le texte de la recommandation est vide")
#
#     return redirect('suivi_detail', pk=suivi_id)

@login_required
def add_traitement_arv(request, suivi_id):
    suivi = get_object_or_404(Suivi, id=suivi_id)
    if request.method == "POST":
        form = TraitementARVForm(request.POST)
        if form.is_valid():
            traitement = form.save(commit=False)
            traitement.suivi = suivi
            traitement.patient = suivi.patient
            traitement.save()
            messages.success(request, "Traitement ARV ajouté avec succès.")
        else:
            messages.error(request, "Erreur lors de l'ajout du traitement ARV.")
    return redirect(reverse('suivis-detail', kwargs={'pk': suivi.id}))


@login_required
def add_suivi_protocole(request, suivi_id):
    suivi = get_object_or_404(Suivi, id=suivi_id)

    if request.method == "POST":
        form = ProtocoleForm(request.POST)
        if form.is_valid():
            protocole = form.save(commit=False)
            protocole.save()
            form.save_m2m()

            # ⚠️ Vérifie que le protocole n’est pas déjà lié
            if SuiviProtocole.objects.filter(suivi=suivi, protocole=protocole).exists():
                messages.warning(request, f"🚫 Ce protocole est déjà lié à ce suivi.")
                return redirect('suivis-detail', pk=suivi.id)

            # Liaison Suivi-Protocole
            SuiviProtocole.objects.create(
                suivi=suivi,
                protocole=protocole,
                nom=protocole.nom,
                description=protocole.description,
                date_debut=protocole.date_debut,
                date_fin=protocole.date_fin,
                created_by=request.user.employee if hasattr(request.user, 'employee') else None
            )

            # Et ici tu passes bien suivi :
            protocole._create_follow_up_actions(
                suivi=suivi,
                created_by=request.user.employee if hasattr(request.user, 'employee') else None
            )

            messages.success(request, "✅ Protocole créé et suivi généré !")
            return redirect('suivis-detail', pk=suivi.id)
        else:
            print(form.errors)
            messages.error(request, "Erreur lors de l'enregistrement du protocole.")

    return redirect(reverse('suivis-detail', kwargs={'pk': suivi.id}))


@login_required
def add_bilan(request, suivi_id):
    suivi = get_object_or_404(Suivi, id=suivi_id)
    if request.method == "POST":
        form = BilanParacliniqueForm(request.POST)
        if form.is_valid():
            bilan = form.save(commit=False)
            bilan.patient = suivi.patient
            bilan.save()
            messages.success(request, "Examen prescrit avec succès.")
        else:
            messages.error(request, "Erreur lors de la prescription de l'examen.")
    return redirect(reverse('suivi_detail', kwargs={'pk': suivi.id}))


@login_required
def add_rdv(request, suivi_id):
    suivi = get_object_or_404(Suivi, id=suivi_id)
    if request.method == "POST":
        form = RendezVousSuiviForm(request.POST)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.patient = suivi.patient
            rdv.save()
            messages.success(request, "Rendez-vous planifié avec succès.")
        else:
            messages.error(request, "Erreur lors de la planification du rendez-vous.")
    return redirect(reverse('suivis-detail', kwargs={'pk': suivi.id}))


class SuiviDetailView(LoginRequiredMixin, DetailView):
    model = Suivi
    template_name = "pages/suivi/suivi_detail.html"
    context_object_name = "suividetail"

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'patient', 'services', 'examens'
        ).prefetch_related(
            Prefetch('suivierdv', queryset=RendezVous.objects.select_related(
                'patient', 'pharmacie', 'service', 'doctor', 'suivi'
            ).prefetch_related('medicaments').order_by('-date', '-time')),
            Prefetch('protocolessuivi', queryset=SuiviProtocole.objects.select_related(
                'protocole', 'protocole__type_protocole'
            ).order_by('protocole__type_protocole__nom')),
            'suivitreatarv',
            'suivicomorbide'
        )

        # Si tu veux filtrer la liste affichée côté tableau
        filter_type = self.request.GET.get('filter')
        if filter_type:
            if filter_type == 'pharmacy':
                qs = qs.filter(services__nom__icontains='pharma')
            elif filter_type == 'consultation':
                qs = qs.filter(services__nom__icontains='consult')
            elif filter_type == 'completed':
                qs = qs.filter(suivierdv__status='Completed')
            elif filter_type == 'upcoming':
                qs = qs.filter(suivierdv__status='Scheduled', suivierdv__date__gte=timezone.now().date())
            elif filter_type == 'missed':
                qs = qs.filter(suivierdv__status='Scheduled', suivierdv__date__lt=timezone.now().date())

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suivi = self.object

        # Générer les recommandations auto si vide
        if not suivi.recommandations_auto:
            suivi.generate_auto_recommandations()
            suivi.save()

        # Grouper protocoles
        protocols = suivi.protocolessuivi.all()
        grouped_protocols = {
            key: list(group) for key, group in groupby(
                protocols,
                key=lambda p: p.protocole.type_protocole
            )
        }

        # Evolution patient
        evolution_data = {
            'dates': [],
            'cd4': [],
            'poids': [],
            'charge_virale': []
        }
        suivis_anterieurs = Suivi.objects.filter(
            patient=suivi.patient
        ).exclude(date_suivi__isnull=True).order_by('date_suivi')

        for s in suivis_anterieurs:
            if s.date_suivi:
                evolution_data['dates'].append(s.date_suivi.strftime("%Y-%m-%d"))
            if s.cd4:
                evolution_data['cd4'].append(s.cd4)
            if s.poids:
                evolution_data['poids'].append(float(s.poids))
            if s.charge_virale:
                evolution_data['charge_virale'].append(s.charge_virale)

        # Comptage RDV
        rdvs = suivi.suivierdv.all()
        context.update({
            'grouped_protocols': grouped_protocols,
            'evolution_data': evolution_data,
            'now': timezone.now(),
            'suivitraitementform': TraitementARVForm(),
            'suiviprotocoleform': SuiviProtocoleForm(),
            'protocoleform': ProtocoleForm(),
            'suivirdvform': RendezVousSuiviForm(),

            'total_rdvs': rdvs.count(),
            'completed_rdvs': rdvs.filter(status='Completed').count(),
            'upcoming_rdvs': rdvs.filter(status='Scheduled', date__gte=timezone.now().date()).count(),
            'missed_rdvs': rdvs.filter(status='Scheduled', date__lt=timezone.now().date()).count(),
        })

        return context


class UrgenceListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = "pages/urgence/urgence_list.html"
    context_object_name = "hurgenceliste"
    paginate_by = 10

    # ordering = "-admission_date"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.request.GET.copy()
        qs.pop('page', True)  # retire le paramètre page s'il existe
        ctx['qs'] = qs.urlencode()  # ex: "status=opened&doctor=12"
        return ctx

    def get_queryset(self):
        # Filtrer les patients dont urgence est True
        return Patient.objects.filter(urgence=True)


class JsonLoginRequiredMixin(AccessMixin):
    """ Comme LoginRequiredMixin mais renvoie JSON 401 au lieu d'un redirect HTML. """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"ok": False, "detail": "Non authentifié."}, status=401)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class UrgenceCreateView(LoginRequiredMixin, TemplateView):
    template_name = "pages/urgence/urgence_create.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from .forms import UrgencePatientForm, UrgenceHospitalizationStep2Form
        ctx['form'] = UrgencePatientForm()
        ctx['step2_form'] = UrgenceHospitalizationStep2Form()
        return ctx


@method_decorator(ensure_csrf_cookie, name="dispatch")
class UrgencePatientCreateAPI(JsonLoginRequiredMixin, View):
    """ Étape 1 (AJAX) — crée le patient en urgence. """

    def post(self, request):
        form = UrgencePatientForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                patient = form.save(commit=False)
                patient.urgence = True
                if hasattr(request.user, 'employee'):
                    patient.created_by = request.user.employee
                patient.save()
                form.save_m2m()
            return JsonResponse({
                "ok": True,
                "patient_id": patient.pk,
                "detail": "Patient enregistré avec succès.",
                "next": reverse('urgence_hosp_api', args=[patient.pk])
            })
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class HospitalizationCreateAPI(JsonLoginRequiredMixin, View):
    """ Étape 2 (AJAX) — crée l'hospitalisation pour un patient donné. """

    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id)
        form = UrgenceHospitalizationStep2Form(request.POST)
        if form.is_valid():
            with transaction.atomic():
                hosp = form.save(commit=False)
                hosp.patient = patient
                hosp.doctor = request.user
                hosp.save()
                form.save_m2m()
            return JsonResponse({

                "ok": True,
                "detail": "Admission en urgence créée avec succès.",
                "redirect": reverse('urgences_list')
            })

        return JsonResponse({"ok": False, "errors": form.errors}, status=400)


# vue corrigée
@login_required
def create_bilan_initial(request, consultation_id, patient_id):
    consultation = get_object_or_404(Consultation, pk=consultation_id)
    patient = get_object_or_404(Patient, pk=patient_id)

    try:
        with transaction.atomic():
            type_bilan, _ = TypeBilanParaclinique.objects.get_or_create(nom="Bilan Initial VIH")

            examens_vih = [
                "CD4",
                "Charge Virale",
                "Hémogramme",
                "Glycémie",
                "Sérologie HBV",
                "Sérologie Syphilis",
            ]

            # Vérifie s'il existe déjà un bilan
            bilan_initial = BilanInitial.objects.filter(
                patient=patient,
                description__icontains="Bilan initial VIH",
                doctor=consultation.doctor
            ).first()

            if not bilan_initial:
                bilan_initial = BilanInitial.objects.create(
                    patient=patient,
                    doctor=consultation.doctor,
                    consultation=consultation,
                    status='pending',
                    description="Bilan initial VIH",
                    priority='medium'
                )

            examens_ajoutes = 0
            prelevements_crees = 0

            for examen_nom in examens_vih:
                examen = ExamenStandard.objects.filter(
                    nom=examen_nom,
                    type_examen=type_bilan
                ).first()

                if not examen:
                    messages.warning(request, f"L'examen '{examen_nom}' n'existe pas pour '{type_bilan}'.")
                    continue

                if not bilan_initial.examens.filter(pk=examen.pk).exists():
                    bilan_initial.examens.add(examen)
                    examens_ajoutes += 1

                # Créer un échantillon seulement si inexistant
                echantillon_existe = Echantillon.objects.filter(
                    consultation=consultation,
                    patient=patient,
                    examen_demande=examen
                ).exists()

                if not echantillon_existe:
                    echantillon = Echantillon.objects.create(
                        code_echantillon=generate_echantillon_code(),
                        examen_demande=examen,
                        patient=patient,
                        consultation=consultation,
                        status_echantillons='Demande',
                    )
                    prelevements_crees += 1

            messages.success(
                request,
                f"✅ {examens_ajoutes} examens ajoutés au bilan et {prelevements_crees} demandes de prélèvement créées."
                if examens_ajoutes or prelevements_crees
                else "⚠️ Aucun nouvel examen ou prélèvement n'a été créé."
            )

    except IntegrityError:
        messages.error(request, "Erreur lors de la création du bilan initial. Veuillez réessayer.")
    except Exception as e:
        messages.error(request, f"Erreur inattendue : {str(e)}")

    return redirect('consultation_detail', pk=consultation_id)


def generate_echantillon_code():
    """
    Génère un code échantillon unique : un entier de 8 chiffres commençant par 2
    """
    import random
    return str(random.randint(20000000, 29999999))


class BilanListView(LoginRequiredMixin, ListView):
    model = BilanInitial
    template_name = 'pages/bilans/bilan_list.html'
    context_object_name = 'bilans'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtre pour les médecins: voir seulement leurs patients
        # if self.request.user.role == 'doctor':
        #     queryset = queryset.filter(doctor=self.request.user)

        # Filtres supplémentaires
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        is_critical = self.request.GET.get('is_critical')
        if is_critical:
            queryset = queryset.filter(is_critical=True)

        return queryset.select_related(
            'patient', 'hospitalization', 'doctor'
        ).prefetch_related(
            'examens'
        )


class BilanDetailView(LoginRequiredMixin, DetailView):
    model = BilanInitial
    template_name = 'pages/bilans/bilan_detail.html'
    context_object_name = 'bilan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bilan = self.object

        # Prépare un mapping examen_id → échantillon (si existant)
        echantillons_map = {}

        for examen in bilan.examens.all():
            echantillon = Echantillon.objects.filter(
                examen_demande=examen,
                patient=bilan.patient,
                consultation=bilan.consultation
            ).order_by('-created_at').first()
            echantillons_map[examen.id] = echantillon

        context['echantillons_map'] = echantillons_map
        return context


class BilanCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BilanInitial
    template_name = 'pages/bilans/bilan_form.html'
    fields = [
        'patient', 'hospitalization', 'examen',
        'description', 'priority', 'comment'
    ]
    permission_required = 'bilans.add_bilaninitial'

    def form_valid(self, form):
        form.instance.doctor = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bilan_detail', kwargs={'pk': self.object.pk})


class BilanUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = BilanInitial
    template_name = 'pages/bilans/bilan_form.html'
    fields = [
        'description', 'priority',
        'comment', 'status', 'result', 'reference_range',
        'unit', 'is_critical'
    ]
    permission_required = 'bilans.change_bilaninitial'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_superuser:
            if self.request.user.role == 'doctor':
                # Les médecins ne peuvent modifier que certains champs
                allowed_fields = ['description', 'priority', 'comment']
                for field in list(form.fields):
                    if field not in allowed_fields:
                        del form.fields[field]
            elif self.request.user.role in ['technician', 'biologist']:
                # Les techniciens peuvent seulement compléter les résultats
                allowed_fields = ['result', 'reference_range', 'unit', 'is_critical']
                for field in list(form.fields):
                    if field not in allowed_fields:
                        del form.fields[field]
        return form

    def form_valid(self, form):
        if 'result' in form.changed_data:
            form.instance.status = 'completed'
            form.instance.technician = self.request.user
            form.instance.result_date = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bilan_detail', kwargs={'pk': self.object.pk})


class BilanDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = BilanInitial
    template_name = 'pages/bilans/bilan_confirm_delete.html'
    success_url = reverse_lazy('bilan_list')
    permission_required = 'bilans.delete_bilaninitial'


class CompleteBilanView(LoginRequiredMixin, UpdateView):
    model = BilanInitial
    template_name = 'pages/bilans/bilan_complete.html'
    fields = ['result', 'reference_range', 'unit', 'is_critical']

    def form_valid(self, form):
        form.instance.status = 'completed'
        form.instance.technician = self.request.user
        form.instance.result_date = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bilan_detail', kwargs={'pk': self.object.pk})
