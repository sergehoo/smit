from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

from smitci import settings
from smitci.utils.ip import client_ip


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Récupérer l'heure de la dernière activité
            last_activity = request.session.get('last_activity')
            now = datetime.now()

            # Vérifier si l'utilisateur a été inactif trop longtemps
            if last_activity:
                last_activity_time = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S.%f')
                if now - last_activity_time > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    logout(request)  # Déconnecter l'utilisateur
                    messages.info(request, "Votre session a expiré en raison d'une inactivité.")
                    return redirect('account_login')  # Rediriger vers la page de connexion

            # Mettre à jour l'heure de la dernière activité
            request.session['last_activity'] = str(now)

        response = self.get_response(request)
        return response


class LogForbiddenMiddleware:
    """Middleware pour journaliser les erreurs 403"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 403:
            print(f"403 Forbidden: {request.path} - Utilisateur : {request.user}")
        return response


class ClientIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.client_ip = client_ip(request)
        return self.get_response(request)
