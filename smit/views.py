import datetime
import os
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime
from itertools import groupby

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Prefetch
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import request, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView
from django_filters.views import FilterView

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus.tables import TableStyle, Table
from six import BytesIO

from core.models import communes_et_quartiers_choices, Location
from pharmacy.models import RendezVous
from smit.filters import PatientFilter
from smit.forms import PatientCreateForm, AppointmentForm, ConstantesForm, ConsultationSendForm, ConsultationCreateForm, \
    SymptomesForm, ExamenForm, PrescriptionForm, AntecedentsMedicauxForm, AllergiesForm, ProtocolesForm, RendezvousForm, \
    ConseilsForm, HospitalizationSendForm, TestRapideVIHForm, EnqueteVihForm, ConsultationForm, EchantillonForm, \
    HospitalizationForm, AppointmentUpdateForm, SuiviSendForm, RdvSuiviForm, UrgencePatientForm, CasContactForm, \
    PatientUpdateForm
from smit.models import Patient, Appointment, Constante, Service, ServiceSubActivity, Consultation, Symptomes, \
    Hospitalization, Suivi, TestRapideVIH, EnqueteVih, Examen, Protocole, SuiviProtocole


# Create your views here.
# Vue API pour envoyer les données à ApexCharts en JSON
def hospitalization_chart_data(request):
    view = HomePageView()
    stats = view.get_hospitalization_statistics()
    return JsonResponse(stats, safe=False)

class HomePageView(LoginRequiredMixin, TemplateView):
    login_url = '/accounts/login/'
    # form_class = LoginForm
    template_name = "pages/home.html"

    def get_patient_age_distribution(self):
        """
        Retourne le nombre de patients par tranche d'âge et sexe.
        """
        current_year = datetime.now().year

        # Définition des tranches d'âge avec leurs limites inférieures et supérieures
        age_groups = [
            ("0-18 ans", 0, 18),
            ("19-25 ans", 19, 25),
            ("26-35 ans", 26, 35),
            ("36-45 ans", 36, 45),
            ("46-60 ans", 46, 60),
            ("61-75 ans", 61, 75),
            ("75 ans et plus", 76, 120),
        ]

        # Initialisation des compteurs
        age_distribution = {group[0]: {"Hommes": 0, "Femmes": 0} for group in age_groups}

        # Récupération des patients avec leur âge et genre
        patients = Patient.objects.values('date_naissance', 'genre')

        for patient in patients:
            if patient['date_naissance']:
                age = current_year - patient['date_naissance'].year
                genre = "Hommes" if patient['genre'] == "Homme" else "Femmes"

                for group_name, min_age, max_age in age_groups:
                    if min_age <= age <= max_age:
                        age_distribution[group_name][genre] += 1
                        break

        return age_distribution

    def get_hospitalization_statistics(self):
        """
        Retourne les statistiques des hospitalisations par période et détaille les statuts spécifiques.
        """
        current_year = datetime.now().year

        # Définition des périodes
        periods = [
            ("Cette semaine", datetime.now() - timedelta(days=7)),
            ("Ce mois", datetime.now().replace(day=1)),
            ("Cette année", datetime(current_year, 1, 1))
        ]

        stats = []

        for label, start_date in periods:
            total_hospitalized = Hospitalization.objects.filter(admission_date__gte=start_date).count()

            # Comptage des cas spécifiques
            total_deaths = Hospitalization.objects.filter(admission_date__gte=start_date, status="DCD").count()
            total_recovered = Hospitalization.objects.filter(admission_date__gte=start_date,
                                                             status="Gueris-EXEA").count()
            total_transferred = Hospitalization.objects.filter(admission_date__gte=start_date,
                                                               status="Transféré-TRANSF").count()
            total_scam = Hospitalization.objects.filter(admission_date__gte=start_date, status="SCAM").count()
            total_evade = Hospitalization.objects.filter(admission_date__gte=start_date, status="EVADE").count()

            death_rate = (total_deaths / total_hospitalized * 100) if total_hospitalized else 0

            stats.append({
                "periode": label,
                "total_hospitalized": total_hospitalized,
                "total_deaths": total_deaths,
                "total_recovered": total_recovered,
                "total_transferred": total_transferred,
                "total_scam": total_scam,
                "total_evade": total_evade,
                "death_rate": round(death_rate, 2)
            })

        # Taux global
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
            "death_rate": round(global_death_rate, 2)
        })

        return stats

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_year = datetime.now().year

        # Monthly patient count for trend graph
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

        # Patient Statistics
        total_patients = Patient.objects.count()
        total_patients_femme = Patient.objects.filter(genre='Femme').count()
        total_patients_homme = Patient.objects.filter(genre='Homme').count()
        patient_status_counts = Patient.objects.values('status').annotate(count=Count('status'))
        average_age = Patient.objects.annotate(age=(datetime.now().year - ExtractYear('date_naissance'))).aggregate(
            Avg('age'))

        # Service Utilization
        consultation_by_service = Consultation.objects.values('services__nom').annotate(count=Count('id'))
        top_services = Service.objects.annotate(total_use=Count('consultations')).order_by('-total_use')[:5]
        recent_consultations = Consultation.objects.select_related('patient', 'services', 'doctor').order_by(
            '-consultation_date')[:10]

        # Appointments Summary
        total_scheduled_appointments = Appointment.objects.filter(status='Scheduled').count()
        appointment_status_counts = Appointment.objects.values('status').annotate(count=Count('status'))
        upcoming_appointments = Appointment.objects.filter(date__gte=datetime.now()).order_by('date')[:10]

        # Hospitalizations Overview
        current_hospitalizations = Hospitalization.objects.filter(discharge_date__isnull=True).count()
        hospitalizations_by_reason = Hospitalization.objects.values('reason_for_admission').annotate(count=Count('id'))
        recent_hospitalizations = Hospitalization.objects.select_related('patient', 'doctor').order_by(
            '-admission_date')[:10]

        # Monthly Trends
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

        context.update({
            "hospitalization_statistics": self.get_hospitalization_statistics(),
            "patient_age_distribution": self.get_patient_age_distribution(),
            "monthly_counts": monthly_counts,
            "total_patients": total_patients,
            "total_patients_femme": total_patients_femme,
            "total_patients_homme": total_patients_homme,
            "patient_status_counts": patient_status_counts,
            "average_age": average_age['age__avg'],
            "consultation_by_service": consultation_by_service,
            "top_services": top_services,
            "recent_consultations": recent_consultations,
            "total_scheduled_appointments": total_scheduled_appointments,
            "appointment_status_counts": appointment_status_counts,
            "upcoming_appointments": upcoming_appointments,
            "current_hospitalizations": current_hospitalizations,
            "hospitalizations_by_reason": hospitalizations_by_reason,
            "recent_hospitalizations": recent_hospitalizations,
            "consultation_counts": consultation_counts,
            "appointment_counts": appointment_counts,
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
        form = RendezvousForm(request.POST)
        if form.is_valid():
            rendezvous = form.save()
            consultation.rendezvous.add(rendezvous)
            consultation.save()
            messages.success(request, 'Rendez-vous ajouté avec succès!')
            return redirect('detail_consultation', pk=consultation.id)
        else:
            messages.error(request, 'Erreur lors de la création du rendez-vous.')
    else:
        form = RendezvousForm()
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


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = "pages/dossier_patient.html"
    context_object_name = "patientsdetail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        services_with_consultations = []

        for service in patient.services_passed:
            consultations = service.consultations.filter(patient=patient)
            services_with_consultations.append((service, consultations))

        context['services_with_consultations'] = services_with_consultations

        # Récupérer les éléments liés au patient
        context["consultations"] = patient.consultation_set.all().order_by('-created_at')
        context["appointments"] = patient.appointments.all().order_by('-created_at')
        context["suivis"] = patient.suivimedecin.all()
        context['case_contacts'] = self.object.case_contacts.all()
        context['cascontactsForm'] = CasContactForm()

        # Ajouter les hospitalisations
        hospitalizations = patient.hospitalized.all().prefetch_related(
            'indicateurs_biologiques',
            'indicateurs_fonctionnels',
            'indicateurs_subjectifs',
            'indicateurs_compliques',
            'indicateurs_autres',
        ).order_by('-created_at')

        context['hospitalizations'] = hospitalizations

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
    ordering = ['-date']

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
        # Filtrer les rendez-vous passés
        today = now().date()
        current_time = now().time()
        return Appointment.objects.filter(date__lt=today, status='Completed') | Appointment.objects.filter(
            date=today, time__lt=current_time
        ).order_by('-date', '-time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()

        # Nombre de rendez-vous passés
        appointments_past_nbr = self.get_queryset().count()

        # Ajouter des données supplémentaires au contexte
        context['salleattente_nbr'] = appointments_past_nbr
        context['salleattente'] = self.get_queryset()
        context['constanteform'] = ConstantesForm()
        context['ConsultationSendForm'] = ConsultationSendForm()

        return context


class ServiceContentDetailView(LoginRequiredMixin, DetailView):
    model = ServiceSubActivity
    # template_name = "pages/services/servicecontent_detail.html"
    context_object_name = "subservice"

    def get_template_names(self):
        # Déterminer le template en fonction du service ou de la sous-activité
        service = self.object.service
        if service.nom == 'VIH/SIDA':
            # if self.object.nom == 'overview':
            #     return ["pages/services/soverview.html"]
            # elif self.object.nom == 'consultation':
            return ["pages/services/servicecontent_detail.html"]
        elif service.nom == 'TUBERCULOSE':
            # if self.object.nom == 'overview':
            #     return ["pages/services/soverview.html"]
            # elif self.object.nom == 'consultation':
            return ["pages/services/consultation.html"]
        else:
            return ["pages/services/servicecontent_default.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.object.service  # Ajoutez le service parent au contexte
        return context


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

        hospitalizations = Hospitalization.objects.filter(activite=subactivity).order_by(
            '-admission_date') if subactivity else []
        hospitalizations_paginator = Paginator(hospitalizations, 10)
        hospitalizations_page = self.request.GET.get('hospitalizations_page')
        context['hospitalizations'] = hospitalizations_paginator.get_page(hospitalizations_page)

        suivis = Suivi.objects.filter(
            services=subactivity.service) if subactivity else []  # Assuming you have a Suivi model
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
        template_map = {
            ('VIH-SIDA', 'Overview'): 'pages/services/VIH-SIDA/vih_sida_overview.html',
            ('VIH-SIDA', 'Consultation'): 'pages/services/VIH-SIDA/consultation_VIH.html',
            ('VIH-SIDA', 'Hospitalisation'): 'pages/services/VIH-SIDA/hospitalisation_VIH.html',
            ('VIH-SIDA', 'Suivi'): 'pages/services/VIH-SIDA/suivi_VIH.html',

            ('COVID', 'Overview'): 'pages/services/COVID/overview_COVID.html',
            ('COVID', 'Consultation'): 'pages/services/COVID/consultation_COVID.html',
            ('COVID', 'Hospitalisation'): 'pages/services/COVID/hospitalisation_COVID.html',
            ('COVID', 'Suivi'): 'pages/services/COVID/suivi_COVID.html',

            ('TUBERCULOSE', 'Overview'): 'pages/services/TUBERCULOSE/overview_TB.html',
            ('TUBERCULOSE', 'Consultation'): 'pages/services/TUBERCULOSE/consultation_TB.html',
            ('TUBERCULOSE', 'Hospitalisation'): 'pages/services/TUBERCULOSE/hospitalisation_TB.html',
            ('TUBERCULOSE', 'Suivi'): 'pages/services/TUBERCULOSE/suivi_TB.html',
        }
        serv = self.kwargs['serv']
        acty = self.kwargs['acty']
        return [template_map.get((serv, acty), 'pages/services/servicecontent_detail.html')]


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
        # context['service'] = self.object.service  # Ajoutez le service parent au contexte
        context['formconsult'] = ConsultationCreateForm()  # Ajoutez le service parent au contexte
        context['examen_form'] = ExamenForm()
        context['prescription_form'] = PrescriptionForm()
        context['antecedentsMedicaux_form'] = AntecedentsMedicauxForm()
        context['allergies_form'] = AllergiesForm()
        context['conseils_form'] = ConseilsForm()
        # context['EnqueteVihForm'] = EnqueteVihForm()
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


class SuiviListView(LoginRequiredMixin, ListView):
    model = Suivi
    template_name = "pages/suivi/suivi_list.html"
    context_object_name = "suivis"


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


class SuiviDetailView(LoginRequiredMixin, DetailView):
    model = Suivi
    template_name = "pages/suivi/suivi_detail.html"
    context_object_name = "suividetail"

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            Prefetch(
                'suivierdv',
                queryset=RendezVous.objects.all()
            ),
            Prefetch(
                'protocolessuivi',
                queryset=SuiviProtocole.objects.select_related('protocole', 'protocole__type_protocole')
                .order_by('protocole__type_protocole__nom')
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Group protocols by their type
        protocols = self.object.protocolessuivi.all()
        grouped_protocols = {
            key: list(group) for key, group in groupby(protocols, key=lambda p: p.protocole.type_protocole)
        }

        # Add grouped protocols to the context
        context['grouped_protocols'] = grouped_protocols
        context['suivirdvform'] = RdvSuiviForm()

        return context


class UrgenceListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = "pages/urgence/urgence_list.html"
    context_object_name = "hurgenceliste"
    paginate_by = 10

    # ordering = "-admission_date"

    def get_queryset(self):
        # Filtrer les patients dont urgence est True
        return Patient.objects.filter(urgence=True)


class UrgenceCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    template_name = "pages/urgence/urgence_create.html"
    form_class = UrgencePatientForm
    success_url = reverse_lazy('urgences_list')  # Rediriger après la création

    def form_valid(self, form):
        # Forcer le champ urgence à True
        form.instance.urgence = True
        form.instance.created_by = self.request.user.employee  # Associer l'utilisateur connecté
        return super().form_valid(form)
