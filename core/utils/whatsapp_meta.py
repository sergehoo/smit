# utils/whatsapp_meta.py
import json
import time
import requests
from django.conf import settings

# Dans settings.py, ajoute (et charge via .env si besoin) :
# META_WA_API_VERSION = "v20.0"            # ou "v21.0" selon ta version
# META_WA_PHONE_NUMBER_ID = "XXXXXXXXXXXX" # ID du numéro WhatsApp (Cloud API)
# META_WA_ACCESS_TOKEN = "EAAG..."         # Permanent token (ou app token régénéré)
# META_WA_BASE_URL = "https://graph.facebook.com"

DEFAULT_TIMEOUT = 15


class WhatsAppMetaError(RuntimeError):
    pass


def _wa_endpoint(path: str) -> str:
    base = getattr(settings, "META_WA_BASE_URL", "https://graph.facebook.com").rstrip("/")
    ver = getattr(settings, "META_WA_API_VERSION", "v20.0").strip("/")
    return f"{base}/{ver}/{path.lstrip('/')}"


def _wa_headers() -> dict:
    token = settings.META_WA_ACCESS_TOKEN
    if not token:
        raise WhatsAppMetaError("META_WA_ACCESS_TOKEN manquant dans settings.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def send_whatsapp_text(recipients, message, preview_url=False):
    """
    Envoi de messages texte (session message) via Meta Cloud API.
    - recipients: liste de MSISDN au format +22507..., PAS de 'whatsapp:' prefix.
    - message: texte brut (<= 4096 chars)
    - preview_url: True pour activer l'aperçu des liens.
    """
    phone_number_id = settings.META_WA_PHONE_NUMBER_ID
    if not phone_number_id:
        raise WhatsAppMetaError("META_WA_PHONE_NUMBER_ID manquant dans settings.")

    url = _wa_endpoint(f"{phone_number_id}/messages")
    headers = _wa_headers()

    # Optionnel : optimisation du texte (si tu as déjà ta fonction)
    try:
        from .sms_utils import optimize_sms_text  # si tu as cette util
        text = optimize_sms_text(message)
    except Exception:
        text = message

    for raw in recipients:
        to = str(raw).strip()
        if not to:
            continue

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text, "preview_url": bool(preview_url)},
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
            if resp.status_code not in (200, 201):
                # Meta renvoie un JSON d’erreur structuré
                raise WhatsAppMetaError(f"HTTP {resp.status_code} - {resp.text}")
            # Log simple (contient message_id)
            print(f"✅ WhatsApp envoyé à {to} | {resp.text}")
        except requests.RequestException as e:
            print(f"❌ Erreur réseau WhatsApp vers {to}: {e}")
        except WhatsAppMetaError as e:
            print(f"❌ Erreur API WhatsApp vers {to}: {e}")


def send_whatsapp_template(recipients, template_name, lang_code="fr", components=None):
    """
    Envoi d’un message TEMPLATE (obligatoire hors fenêtre 24h ou pour push proactif).
    - template_name: nom validé dans Business Manager (ex: 'otp_verification')
    - lang_code: code de langue (ex: 'fr', 'fr_FR', 'en_US'), tel que validé avec le template
    - components: liste de composants (header/body/buttons) selon le template Meta, ex:
        components = [
          {"type": "body", "parameters": [{"type": "text", "text": "Serge"}]}
        ]
    """
    phone_number_id = settings.META_WA_PHONE_NUMBER_ID
    if not phone_number_id:
        raise WhatsAppMetaError("META_WA_PHONE_NUMBER_ID manquant dans settings.")

    url = _wa_endpoint(f"{phone_number_id}/messages")
    headers = _wa_headers()

    tpl = {
        "name": template_name,
        "language": {"code": lang_code},
    }
    if components:
        tpl["components"] = components

    for raw in recipients:
        to = str(raw).strip()
        if not to:
            continue

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": tpl,
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
            if resp.status_code not in (200, 201):
                raise WhatsAppMetaError(f"HTTP {resp.status_code} - {resp.text}")
            print(f"✅ WhatsApp TEMPLATE envoyé à {to} | {resp.text}")
        except requests.RequestException as e:
            print(f"❌ Erreur réseau WhatsApp (template) vers {to}: {e}")
        except WhatsAppMetaError as e:
            print(f"❌ Erreur API WhatsApp (template) vers {to}: {e}")
