# core/utils/ip.py
from __future__ import annotations

from ipware import get_client_ip

# Liste d'adresses/ranges de proxys de confiance (Traefik + éventuels LB/Cloudflare)
# ⚠️ Mets-y tes subnets internes Docker (ex: 172.18.0.0/16) et, si tu passes par Cloudflare,
# leurs ranges publiques. Garde ça court au début; tu pourras élargir ensuite.
TRUSTED_PROXIES = [
    "127.0.0.1",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "172.22.0.17/16",
    # "173.245.48.0/20", "103.21.244.0/22", ...  # (Cloudflare, si utilisé)
]


def client_ip(request) -> str | None:
    """
    Retourne l'IP client *réelle* si possible, sinon None.
    - ipware lit proprement CF-Connecting-IP, X-Forwarded-For, X-Real-IP, etc.
    - On lui passe la liste de proxys de confiance pour éviter le spoof.
    """
    ip, route = get_client_ip(
        request,
        proxy_trusted_ips=TRUSTED_PROXIES,  # ipware n'utilisera les headers que si la chaîne vient d'un proxy “trusted”
    )
    return ip
