import logging

from django.utils.deprecation import MiddlewareMixin
from django_user_agents.utils import get_user_agent
from django.core.cache import cache
from user_agents import parse
from core.models import VisitCounter

logger = logging.getLogger(__name__)


class VisitCounterMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Ignorer les IP locales et privées
        if ip in ["127.0.0.1", "::1"] or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.16."):
            return

        # Détection du type d'appareil
        user_agent_data = parse(user_agent)
        is_mobile = user_agent_data.is_mobile
        is_tablet = user_agent_data.is_tablet
        is_pc = not is_mobile and not is_tablet  # Si ce n'est pas mobile ni tablette, c'est un PC

        # Vérifie si l'utilisateur est connecté
        user = request.user if request.user.is_authenticated else None

        # Éviter les enregistrements en double trop fréquents (ex: une visite par minute par IP)
        cache_key = f"visit_{ip}"
        if cache.get(cache_key):
            return  # Si l'IP est déjà enregistrée récemment, on ignore cette requête

        try:
            VisitCounter.objects.create(
                ip_address=ip,
                user_agent=user_agent,
                user=user,
                is_mobile=is_mobile,
                is_tablet=is_tablet,
                is_pc=is_pc,
            )
            cache.set(cache_key, True, timeout=60)  # Empêche une nouvelle entrée pendant 60s
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de la visite: {e}")

    def get_client_ip(self, request):
        """Récupère l'adresse IP du visiteur."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '').strip()
        return ip
