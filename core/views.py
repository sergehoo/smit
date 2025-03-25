import base64
import io
import json
from datetime import timedelta

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from matplotlib import pyplot as plt

from core.models import Employee, VisitCounter
from smit.forms import RoleForm, AssignRoleForm, EmployeeCreateForm
from twilio.rest import Client
import random
import string
from django.contrib.auth.models import User


# Create your views here.
def custom_403_view(request, exception=None):
    """Vue personnalisée pour les erreurs 403"""
    return HttpResponseForbidden(
        "<h1>Erreur 403 - Accès interdit</h1>"
        "<p>Vous n'avez pas les permissions nécessaires pour accéder à cette ressource.</p>"
        f"<p>Utilisateur connecté : {request.user}</p>"
        f"<p>Permissions actuelles : {request.user.get_all_permissions()}</p>"
    )


def protected_view(request):
    if not request.user.has_perm('app_name.view_resource'):
        raise PermissionDenied("Vous n'avez pas la permission de consulter cette ressource.")
    return HttpResponse("Ressource protégée.")


class RoleListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "roles/role_list.html"
    context_object_name = "roles"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     form = RoleForm()
    #     context['rolesform'] = form
    #     context['grouped_permissions'] = form.get_permissions_grouped_by_model()
    #     grouped_permissions = {}
    #
    #     # Grouper les permissions par content_type (fonctionnalité)
    #     for role in Group.objects.all():
    #         for perm in role.permissions.all():
    #             model_name = perm.content_type.model
    #             if model_name not in grouped_permissions:
    #                 grouped_permissions[model_name] = []
    #             grouped_permissions[model_name].append(perm)
    #
    #     context['grouped_permissions'] = grouped_permissions
    #     return context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = RoleForm()
        context['rolesform'] = form
        context['grouped_permissions'] = form.get_permissions_grouped_by_model()  # Appel direct pour grouper
        return context


class RoleCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = RoleForm
    success_url = reverse_lazy('user_role')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.permissions.set(form.cleaned_data['permissions'])
        self.object.save()
        return response


class RoleUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = RoleForm
    template_name = "roles/role_update.html"
    success_url = reverse_lazy('user_role')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.permissions.set(form.cleaned_data['permissions'])
        self.object.save()
        return response


class RoleDeleteView(LoginRequiredMixin, DeleteView):
    model = Group
    template_name = "roles/role_confirm_delete.html"
    success_url = reverse_lazy('user_role')

    def form_valid(self, form):
        # Créer l'employé
        response = super().form_valid(form)
        messages.success(self.request, "Role supprimer avec successfully")
        return response


class AssignRoleView(LoginRequiredMixin, FormView):
    form_class = AssignRoleForm
    template_name = "roles/assign_role.html"
    success_url = reverse_lazy("role_list")

    def form_valid(self, form):
        employee_id = self.kwargs.get("pk")
        employee = get_object_or_404(Employee, pk=employee_id)
        role = form.cleaned_data["role"]
        employee.user.groups.add(role)
        return super().form_valid(form)


@login_required
def employee_profile(request):
    """Affiche le profil de l'employé connecté"""
    employee = get_object_or_404(Employee, user=request.user)
    return render(request, "employees/profile.html", {"employee": employee})


class EmployeeListView(PermissionRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 10
    ordering = ['user__first_name', 'user__last_name']
    permission_required = 'core.can_view_employee'

    def get_queryset(self):
        # Récupérer tous les employés
        queryset = super().get_queryset()

        # Récupérer le paramètre de recherche
        search_query = self.request.GET.get('search', '')

        # Filtrer les employés si une recherche est effectuée
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')  # Ajouter la recherche au contexte
        return context

    # def get_ordering(self):
    #     # Récupère l'ordre de tri à partir de l'URL ou utilise 'nom' par défaut
    #     return self.request.GET.get('ordering', 'nom')


def generate_password(length=8):
    """Génère un mot de passe aléatoire avec seulement des chiffres et des lettres minuscules"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))


# API URLs
ORANGE_API_TOKEN_URL = "https://api.orange.com/oauth/v3/token"
ORANGE_SMS_API_URL = "https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B2250709862860/requests"  # Remplacez +2250000

# Vos informations d'identification
CLIENT_ID = "T2fHXIzNPGLmj63wy1nOxDrDKJPIb4Wy"
CLIENT_SECRET = "6cKzYeAGdDMMTYTWvgSqLEnwYtU9AkQQZRZin0dIPaNX"
AUTHORIZATION_HEADER = "Basic VDJmSFhJek5QR0xtajYzd3kxbk94RHJES0pQSWI0V3k6NmNLelllQUdkRE1NVFlUV3ZnU3FMRW53WXRVOUFrUVFaUlppbjBkSVBhTlg="  # Remplacez par votre Authorization Header
SENDER_PHONE = "2250709862860"  # Remplacez par votre numéro autorisé


def get_orange_access_token():
    """Obtenir un token d'accès pour l'API SMS d'Orange"""
    headers = {
        "Authorization": AUTHORIZATION_HEADER,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(ORANGE_API_TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        access_token = response.json().get("access_token")
        # print(f"Access Token obtenu : {access_token}")
        return access_token
    else:
        raise Exception(f"Erreur lors de la récupération du token : {response.text}")


def send_sms_with_orange(phone_number, message):
    """Envoie un SMS via l'API Orange CI"""
    try:
        # Obtenez le token d'accès
        access_token = get_orange_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "outboundSMSMessageRequest": {
                "address": f"tel:+{phone_number}",
                "senderAddress": f"tel:+{SENDER_PHONE}",
                "outboundSMSTextMessage": {"message": message},
            }
        }

        response = requests.post(ORANGE_SMS_API_URL, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"SMS envoyé avec succès à {phone_number}")
            return True
        else:
            print(f"Erreur lors de l'envoi du SMS : {response.text}")
            return False

    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
        return False


def notify_employee_with_sms(employee):
    """Notifier un employé via SMS"""
    # Générer un mot de passe temporaire
    default_password = generate_password()

    # Mettre à jour le mot de passe de l'utilisateur
    employee.user.set_password(default_password)
    employee.user.save()

    # Contenu du SMS
    message_body = (
        f"SMIT (Service des Maladies Infestieuses et Tropical).\n"
        f"Bonjour {employee.user.first_name},\n"
        f"Votre compte SMIT est activé avec succès.\n"
        f"Login: {employee.user.username}\n"
        f"Mot de passe: {default_password}\n"
        f"Merci de le modifier dès votre connexion."
    )

    # Envoi du SMS
    if send_sms_with_orange(employee.phone, message_body):
        print(f"Notification envoyée à {employee.phone}")
    else:
        print(f"Échec de l'envoi du SMS à {employee.phone}")


def send_sms_view(request, employee_id):
    """Vue pour envoyer un SMS à un employé"""
    employee = get_object_or_404(Employee, id=employee_id)

    if not employee.phone:
        # return JsonResponse({"error": "L'employé n'a pas de numéro de téléphone."}, status=400)
        messages.error(request, 'L\'employé n\'a pas de numéro de téléphone.')
        return redirect('employee_list')

    notify_employee_with_sms(employee)

    messages.success(request, 'SMS envoyé avec succès.')

    return redirect('employee_list')
    # return JsonResponse({"success": "SMS envoyé avec succès."})


token = get_orange_access_token()


# print(f"Access Token : {token}")


def check_sms_balance():
    """Vérifie le solde de crédits SMS"""
    access_token = get_orange_access_token()  # Ajout des parenthèses pour appeler la fonction
    url = "https://api.orange.com/sms/admin/v1/contracts"  # URL pour vérifier le contrat

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Afficher la réponse avec formatage JSON
        formatted_response = json.dumps(response.json(), indent=4, ensure_ascii=False)
        # print("Détails du contrat :\n", formatted_response)
        return response.json()
    else:
        # Afficher les erreurs avec retour à la ligne
        # print(f"Erreur lors de la vérification des crédits :\n{response.text}")
        return None


# Exécutez la fonction
# check_sms_balance()


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeCreateForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employee_list")
    permission_required = 'can_view_employee'

    def form_valid(self, form):
        # Créer l'utilisateur
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        role = form.cleaned_data['role']

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # Associer le rôle à l'utilisateur
        user.groups.add(role)

        # Créer l'employé en associant l'utilisateur
        employee = form.save(commit=False)
        employee.user = user
        employee.save()
        messages.success(self.request, "Employee creer avec successfully")
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeCreateForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employee_list")

    def form_valid(self, form):
        # Créer l'employé
        response = super().form_valid(form)
        role = form.cleaned_data["role"]
        self.object.user.groups.add(role)
        return response


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = "roles/employee_confirm_delete.html"
    success_url = reverse_lazy('employee_list')

    def form_valid(self, form):
        # Créer l'employé
        response = super().form_valid(form)
        messages.success(self.request, "Employee supprimer avec successfully")
        return response


def generate_visit_chart():
    last_week = now() - timedelta(days=7)
    visits_per_day = (
        VisitCounter.objects.filter(timestamp__gte=last_week)
        .values('timestamp__date')
        .annotate(total_visits=models.Count('id'))
        .order_by('timestamp__date')
    )

    days = [entry['timestamp__date'].strftime('%Y-%m-%d') for entry in visits_per_day]
    visit_counts = [entry['total_visits'] for entry in visits_per_day]

    plt.figure(figsize=(8, 4))
    plt.plot(days, visit_counts, marker="o", linestyle="-", label="Visites")
    plt.xlabel("Date")
    plt.ylabel("Nombre de visites")
    plt.title("Nombre de visites par jour (7 derniers jours)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()

    return graphic


def dashboard_view(request):
    visit_chart = generate_visit_chart()
    return render(request, "admin/dashboard.html", {"visit_chart": visit_chart})
