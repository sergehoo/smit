import os
from datetime import date, timedelta

import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import request, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
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
    ConseilsForm, HospitalizationSendForm, TestRapideVIHForm, EnqueteVihForm, ConsultationForm, EchantillonForm
from smit.models import Patient, Appointment, Constante, Service, ServiceSubActivity, Consultation, Symptomes, \
    Hospitalization, Suivi, TestRapideVIH, EnqueteVih, Examen


# Create your views here.

class HomePageView(LoginRequiredMixin, TemplateView):
    login_url = '/accounts/login/'
    # form_class = LoginForm
    template_name = "pages/home.html"

    # # Call the parent class's dispatch method for normal view processing.
    #     return super().dispatch(request, *args, **kwargs)
    #
    # def dispatch(self, request, *args, **kwargs):
    #     # Call the parent class's dispatch method for normal view processing.
    #     response = super().dispatch(request, *args, **kwargs)
    #
    #     # Check if the user is authenticated. If not, redirect to the login page.
    #     if not request.user.is_authenticated:
    #         return redirect('login')
    #
    #     # Check if the user is a member of the RH Managers group
    #     if request.user.groups.filter(name='ressources_humaines').exists():
    #         # Redirect the user to the RH Managers dashboard
    #         return redirect('rhdash')
    #
    #     # Check if the user is a member of the RH Employees group
    #     elif request.user.groups.filter(name='project').exists():
    #         # Redirect the user to the RH Employees dashboard
    #         return redirect('rh_employee_dashboard')
    #
    #     # If the user is not a member of any specific group, return a forbidden response
    #     else:
    #         return redirect('page_not_found')
    #         # return HttpResponseForbidden("You don't have permission to access this page.")


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


def create_consultation_pdf(request, patient_id, consultation_id):
    # Récupérer la consultation et l'enquête VIH associée
    consultation = get_object_or_404(Consultation, id=consultation_id)
    patient = consultation.patient
    doctor = consultation.doctor if consultation.doctor else 'Inconnu'
    enquete_vih = EnqueteVih.objects.filter(consultation=consultation).first()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Consultation_{consultation_id}_Patient_{patient.nom}.pdf"'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)  # Mode portrait

    # Charger les images
    logo_path = os.path.join(settings.STATIC_ROOT, 'images/logoMSHPCMU.jpg')
    logo_ci = os.path.join(settings.STATIC_ROOT, 'images/armoirieci.jpg')
    watermark_path = os.path.join(settings.STATIC_ROOT, 'images/logokeneya260.png')
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
        c.setFillAlpha(0.1)  # Ajustez la transparence du filigrane ici
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
    # c.drawString(16 * cm, height - 2 * cm, "République de Côte d'Ivoire")  # Texte à droite
    c.drawString(16.2 * cm, height - 2.3 * cm, "Union-Discipline-Travail")  # Texte à droite

    c.setFont("Helvetica-Bold", 12)
    c.drawString(5 * cm, height - 5 * cm, "FICHE DE SUIVIE DES PERSONNES VIVANT AVEC LE VIH")  # Texte à droite
    c.line(5 * cm, height - 5.2 * cm, width - 4 * cm, height - 5.2 * cm)

    # Ajouter une ligne pour séparer l'en-tête du contenu
    # c.line(1 * cm, height - 2.2 * cm, width - 1 * cm, height - 2.2 * cm)

    c.setFont("Helvetica-Bold", 8)
    c.drawString(2.5 * cm, height - 6 * cm, "SUI 01 .")  # Texte à gauche
    c.drawString(2.5 * cm, height - 6.5 * cm, "SUI 02 .")  # Texte à gauche
    c.drawString(2.5 * cm, height - 7 * cm, "SUI 03 .")  # Texte à gauche
    c.drawString(2.5 * cm, height - 7.5 * cm, "SUI 04 .")  # Texte à gauche
    c.drawString(2.5 * cm, height - 8 * cm, "SUI 05 .")  # Texte à gauche
    c.drawString(2.5 * cm, height - 8.5 * cm, "SUI 06 .")  # Texte à gauche
    c.drawString(2.5 * cm, height - 9 * cm, "SUI 07 .")  # Texte à gauche

    c.setFont("Helvetica", 8)
    c.drawString(0.4 * cm, height - 6 * cm, "(DINTV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 6.5 * cm, "(SUJETNO)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 7 * cm, "(LABNO)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 7.5 * cm, "(NOMSERV)")  # Texte à gauche
    c.drawString(0.4 * cm, height - 8 * cm, "(SERVICE)")  # Texte à gauche

    # Position de départ pour le formulaire
    y_position = height - 6 * cm
    line_height = 0.5 * cm

    # Fonction pour dessiner une ligne de formulaire avec pointillés
    c.setFont("Helvetica", 8)

    def draw_form_line(label, value):
        nonlocal y_position
        c.drawString(4 * cm, y_position, f"{label}:")
        c.drawString(9 * cm, y_position, str(value) if value else '______________________________')
        c.setDash(1, 2)  # Pointillé
        c.line(9 * cm, y_position - 0.2 * cm, width - 2 * cm, y_position - 0.2 * cm)
        c.setDash()  # Réinitialiser les lignes normales
        y_position -= line_height

    # Informations de la consultation sous forme de lignes de formulaire
    draw_form_line("Code VIH", patient.code_vih)
    draw_form_line("Nom", patient.nom)
    draw_form_line("Prenom", patient.prenoms)

    draw_form_line("SUI 04. Médecin", doctor)
    draw_form_line("SUI 05. Date de consultation", consultation.consultation_date.strftime('%d-%m-%Y %H:%M'))
    draw_form_line("Diagnostic", consultation.diagnosis)
    draw_form_line("Commentaires", consultation.commentaires)

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
    consultation.hospitalised = 1
    consultation.requested_at = date.today()
    consultation.save()
    messages.success(request, 'La demandena ete transmise avec succes!')

    # Rediriger vers une vue appropriée après la mise à jour
    # Par exemple, rediriger vers la page des détails du patient ou une liste de consultations
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


# def enquete_create(request, consultation_id):
#     consultation = get_object_or_404(Consultation, id=consultation_id)
#     if request.method == 'POST':
#         form = EnqueteVihForm(request.POST)
#         if form.is_valid():
#             enquete = form.save(commit=False)
#             enquete.patient = consultation.patient
#             enquete.consultation = consultation
#             enquete.save()
#             messages.success(request, 'Enquête VIH créée avec succès!')
#
#             return redirect('detail_consultation', pk=consultation.id)
#         else:
#             messages.error(request, 'Erreur lors de la création de l\'Enquête.')
#     else:
#         form = AntecedentsMedicauxForm()
#     return redirect('detail_consultation', pk=consultation.id)
#

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


# @login_required
# def create_appointment(request, patient_id):
#     patient = get_object_or_404(Patient, id=patient_id)
#     if request.method == 'POST':
#         form = AppointmentForm(request.POST)
#         if form.is_valid():
#             calendar = Calendar.objects.get(name='appointments')
#             event = Event.objects.create(
#                 title='Appointment with {}'.format(patient.nom),
#                 start=form.cleaned_data['start'],
#                 end=form.cleaned_data['end'],
#                 calendar=calendar
#             )
#             Appointment.objects.create(patient=patient, calendar=calendar, event=event, notes=form.cleaned_data['notes'])
#             return redirect('appointment_list')
#     else:
#         form = AppointmentForm()
#     return render(request, 'create_appointment.html', {'form': form, 'patient': patient})

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


# class ConstanteCreateView(LoginRequiredMixin, CreateView):
#     model = Constante
#     form_class = ConstantesForm
#     template_name = "pages/constantes/constntes_form.html"
#     success_url = reverse_lazy('attente')
#
#     def get_initial(self):
#         patient_id = self.kwargs['patient_id']
#         patient = get_object_or_404(Patient, id=patient_id)
#         return {'patient': patient}
#
#     def form_valid(self, form):
#         patient_id = self.kwargs['patient_id']
#         patient = get_object_or_404(Patient, id=patient_id)
#         form.instance.patient = patient
#         form.instance.created_by = request.user.employee
#         return super().form_valid(form)

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
        return context


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientCreateForm
    template_name = "pages/patient_create.html"
    success_url = reverse_lazy('global_search')  # Ensure 'global_search' points to your desired view

    def form_valid(self, form):
        nom = form.cleaned_data['nom'].upper()
        prenoms = form.cleaned_data['prenoms'].upper()
        date_naissance = form.cleaned_data['date_naissance']
        contact = form.cleaned_data['contact']

        # Vérification des doublons
        if Patient.objects.filter(nom__iexact=nom, prenoms__iexact=prenoms, date_naissance=date_naissance).exists():
            messages.error(self.request, 'Ce patient existe déjà.')
            return self.form_invalid(form)

        if Patient.objects.filter(contact=contact).exists():
            messages.error(self.request, 'Un patient avec ce contact existe déjà.')
            return self.form_invalid(form)

        # new_commune = form.cleaned_data['new_commune'].strip()

        # Check if the new commune is not in the existing choices
        # if new_commune and not Location.objects.filter(commune=new_commune).exists():
        #     Location.objects.create(commune=new_commune)
        # Optionally, you can update the choice list dynamically

        # Save the Patient object
        self.object = form.save()

        # Handle the Location information
        location_data = {
            'contry': form.cleaned_data['pays'],
            'commune': form.cleaned_data['commune']
        }
        location_instance, created = Location.objects.get_or_create(**location_data)
        self.object.localite = location_instance
        self.object.save()

        messages.success(self.request, 'Patient créé avec succès!')
        return redirect(self.success_url)


class RendezVousListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = "pages/appointments/appointment_list.html"
    context_object_name = "rendezvous"
    paginate_by = 10
    ordering = ['-date']


class RendezVousDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = "pages/appointments/appointment_detail.html"
    context_object_name = "rendezvousdetails"
    paginate_by = 10
    ordering = ['-id']


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
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     today = date.today()
    #     appointments = Appointment.objects.filter(date=today).order_by('time')
    #
    #     # Récupérer la dernière constante pour chaque patient
    #     constantes = {appointment.patient.id: Constante.objects.filter(patient=appointment.patient).order_by('-created_at').first() for appointment in appointments}
    #
    #     # Vérification des valeurs de constantes et génération des alertes
    #     alerts = {}
    #     for patient_id, constante in constantes.items():
    #         if constante:
    #             patient_alerts = []
    #             if constante.tension_systolique and (
    #                     constante.tension_systolique < 90 or constante.tension_systolique > 120):
    #                 patient_alerts.append(('tension_systolique', 'Tension artérielle systolique anormale.'))
    #             if constante.tension_diastolique and (
    #                     constante.tension_diastolique < 60 or constante.tension_diastolique > 80):
    #                 patient_alerts.append(('tension_diastolique', 'Tension artérielle diastolique anormale.'))
    #             if constante.frequence_cardiaque and (
    #                     constante.frequence_cardiaque < 60 or constante.frequence_cardiaque > 100):
    #                 patient_alerts.append(('frequence_cardiaque', 'Fréquence cardiaque anormale.'))
    #             if constante.frequence_respiratoire and (
    #                     constante.frequence_respiratoire < 12 or constante.frequence_respiratoire > 20):
    #                 patient_alerts.append(('frequence_respiratoire', 'Fréquence respiratoire anormale.'))
    #             if constante.temperature and (constante.temperature < 36.1 or constante.temperature > 37.2):
    #                 patient_alerts.append(('temperature', 'Température anormale.'))
    #             if constante.saturation_oxygene and (
    #                     constante.saturation_oxygene < 95 or constante.saturation_oxygene > 100):
    #                 patient_alerts.append(('saturation_oxygene', 'Saturation en oxygène anormale.'))
    #             if constante.glycemie and (constante.glycemie < 70 or constante.glycemie > 140):
    #                 patient_alerts.append(('glycemie', 'Glycémie anormale.'))
    #
    #             if patient_alerts:
    #                 alerts[patient_id] = patient_alerts
    #
    #     context['salleattente'] = appointments
    #     context['constantes'] = constantes
    #     context['constanteform'] = ConstantesForm()
    #     context['alerts'] = alerts
    #
    #     return context


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


# class ActiviteListView(ListView):
#     context_object_name = 'activities'
#
#     def get_queryset(self):
#         serv = self.kwargs['serv']
#         acty = self.kwargs['acty']
#         return ServiceSubActivity.objects.filter(service__nom=serv, nom=acty)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         serv = self.kwargs['serv']
#         acty = self.kwargs['acty']
#         acty_id = self.kwargs['acty_id']
#
#         subactivity = ServiceSubActivity.objects.filter(service__nom=serv, nom=acty, id=acty_id).first()
#         consultations = Consultation.objects.filter(activite=subactivity) if subactivity else []
#
#         context.update({
#             'serv': serv,
#             'acty': acty,
#             'acty_id': acty_id,
#             'subactivity': subactivity,
#             'consultations': consultations,
#         })
#         return context
#
#     def get_template_names(self):
#         template_map = {
#             ('VIH-SIDA', 'Overview'): 'pages/services/vih_sida_overview.html',
#             ('VIH-SIDA', 'Consultation'): 'pages/services/consultation_VIH.html',
#             ('VIH-SIDA', 'Hospitalisation'): 'pages/services/consultation_VIH.html',
#             ('VIH-SIDA', 'Suivi'): 'pages/services/consultation_VIH.html',
#
#             ('COVID', 'Overview'): 'pages/services/consultation_COVID.html',
#             ('COVID', 'Consultation'): 'pages/services/consultation_COVID.html',
#             ('COVID', 'Hospitalisation'): 'pages/services/consultation_COVID.html',
#             ('COVID', 'Suivi'): 'pages/services/consultation_COVID.html',
#
#             ('TUBERCULOSE', 'Overview'): 'pages/services/consultation_COVID.html',
#             ('TUBERCULOSE', 'Consultation'): 'pages/services/consultation_COVID.html',
#             ('TUBERCULOSE', 'Hospitalisation'): 'pages/services/consultation_COVID.html',
#             ('TUBERCULOSE', 'Suivi'): 'pages/services/consultation_COVID.html',
#         }
#         serv = self.kwargs['serv']
#         acty = self.kwargs['acty']
#         return [template_map.get((serv, acty), 'pages/services/servicecontent_detail.html')]
class ActiviteListView(ListView):
    context_object_name = 'activities'
    ordering = ['created_at']
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
        hospitalizations = Hospitalization.objects.filter(activite=subactivity) if subactivity else []
        suivis = Suivi.objects.filter(activite=subactivity) if subactivity else []  # Assuming you have a Suivi model

        context.update({
            'serv': serv,
            'acty': acty,
            'acty_id': acty_id,
            'subactivity': subactivity,
            'consultations': consultations,
            'hospitalizations': hospitalizations,
            'suivis': suivis,
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


class ConsultationListView(ListView):
    model = Consultation
    template_name = 'consultations/consultation_list.html'  # Chemin vers votre template
    context_object_name = 'consultations'
    ordering = ['-consultation_date']
    paginate_by = 10


class ConsultationDetailView(DetailView):
    model = Consultation
    template_name = 'consultations/consultation_detail.html'
    context_object_name = 'consultation'


class ConsultationUpdateView(UpdateView):
    model = Consultation
    form_class = ConsultationForm
    template_name = 'consultations/consultation_form.html'

    def get_success_url(self):
        return reverse_lazy('consultation_detail', kwargs={'pk': self.object.pk})


class ConsultationDeleteView(DeleteView):
    model = Consultation
    template_name = 'consultations/consultation_confirm_delete.html'
    success_url = reverse_lazy('consultation_list')


class ConsultationSidaListView(LoginRequiredMixin, ListView):
    model = Consultation
    template_name = "pages/services/consultation_VIH.html"
    context_object_name = "consultations_vih"


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


def delete_test_rapide_vih(request, test_id, consultation_id):
    # Récupérer l'objet TestRapideVIH avec l'id fourni
    test_rapide = get_object_or_404(TestRapideVIH, id=test_id)
    consultation = get_object_or_404(Consultation, id=consultation_id)

    # Vérifie que la requête est bien une requête POST (pour éviter les suppressions accidentelles)

    test_rapide.delete()
    messages.success(request, 'Le test rapide VIH a été supprimé avec succès.')
    # Redirection après suppression (à personnaliser selon vos besoins)
    return redirect('detail_consultation', pk=consultation.id)


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
        context['depistage_form'] = TestRapideVIHForm()
        context['prelevement_form'] = EchantillonForm()

        context['symptomes_form'] = SymptomesForm()
        context['symptomes_forms'] = [SymptomesForm(prefix=str(i)) for i in range(1)]
        return context
