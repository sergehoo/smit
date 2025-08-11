import copy
import os
import unicodedata
import time
import requests
from twilio.rest import Client
from django.conf import settings
from urllib.parse import quote

_TOKEN_CACHE = {"value": None, "exp": 0}

ORANGE_TOKEN_URL = "https://api.orange.com/oauth/v3/token"
ORANGE_SMS_URL = "https://api.orange.com/smsmessaging/v1/outbound/{}/requests"


def get_orange_sms_token():
    # cache simple
    if _TOKEN_CACHE["value"] and _TOKEN_CACHE["exp"] > time.time() + 30:
        return _TOKEN_CACHE["value"]

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {"grant_type": "client_credentials"}

    r = requests.post(
        settings.ORANGE_TOKEN_URL,            # "https://api.orange.com/oauth/v3/token"
        data=data,
        headers=headers,
        auth=(settings.ORANGE_SMS_CLIENT_ID, settings.ORANGE_SMS_CLIENT_SECRET),
        timeout=15,
    )
    if r.status_code == 401:
        raise RuntimeError(f"Orange OAuth 401: {r.text}")
    r.raise_for_status()

    payload = r.json()
    token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 3600))
    _TOKEN_CACHE["value"] = token
    _TOKEN_CACHE["exp"] = time.time() + expires_in
    return token

def optimize_sms_text(text, max_length=160):
    """
    Optimise le contenu d'un SMS :
    - Supprime les accents (pour rester GSM-7)
    - Évite les emojis et symboles non pris en charge
    - Coupe proprement à la longueur souhaitée (par défaut 160 caractères)
    """

    # Supprimer les accents et caractères Unicode
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()

    # Nettoyage de caractères spéciaux
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('–', '-')

    # Coupe le texte proprement si trop long
    if len(text) > max_length:
        text = text[:max_length - 3] + '...'

    return text.strip()


# def send_sms(recipients, message):
#     access_token = get_orange_sms_token()
#     sender_address = settings.ORANGE_SMS_SENDER.strip()  # ex: 'tel:+22507XXXXXXX'
#     sms_url = settings.ORANGE_SMS_URL.format(sender_address)
#
#     headers = {
#         "Authorization": f"Bearer {access_token}",
#         "Accept": "application/json",          # IMPORTANT
#         "Content-Type": "application/json"
#     }
#
#     # on n'optimise qu'une fois
#     safe_text = optimize_sms_text(message)
#
#     payload_template = {
#         "outboundSMSMessageRequest": {
#             "address": "",  # on remplit par destinataire
#             "senderAddress": sender_address,
#             "outboundSMSTextMessage": {"message": safe_text},
#             # ⚠️ 'senderName' n'est pas accepté librement. Voir note ci-dessous.
#         }
#     }
#
#     for raw_number in recipients:
#         number = str(raw_number).strip()
#         if not number:
#             continue
#
#         # Format MSISDN Orange
#         recipient_address = f"tel:{number}"
#
#         # deep copy pour éviter les effets de bord
#         payload = copy.deepcopy(payload_template)
#         payload["outboundSMSMessageRequest"]["address"] = recipient_address
#
#         try:
#             resp = requests.post(sms_url, headers=headers, json=payload, timeout=20)
#             # Orange renvoie souvent 201 Created
#             if resp.status_code not in (200, 201):
#                 print(f"❌ Orange SMS API -> {resp.status_code} : {resp.text}")
#                 resp.raise_for_status()
#             print(f"✅ SMS envoyé à {number}")
#         except requests.RequestException as e:
#             # log détaillé
#             print(f"❌ Erreur SMS Orange vers {number} : {e}")

# def send_sms(recipients, message):
#     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#
#     for number in recipients:
#         try:
#             client.messages.create(
#                 messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
#                 body=message,
#                 # from_=settings.TWILIO_PHONE_NUMBER,
#                 to=number
#             )
#         except Exception as e:
#             print(f"Erreur d'envoi du SMS à {number}: {str(e)}")
def send_sms(recipients, message):
    token = get_orange_sms_token()

    # ⚠️ Doit être le shortcode/numéro provisionné (ex: 'tel:+225734201')
    sender_address = settings.ORANGE_SMS_SENDER.strip()
    sender_path = quote(sender_address, safe=':+')  # encode proprement le path

    sms_url = settings.ORANGE_SMS_URL.format(sender_path)  # "https://api.orange.com/smsmessaging/v1/outbound/{}/requests"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    safe_text = optimize_sms_text(message)

    # modèle de base
    payload_template = {
        "outboundSMSMessageRequest": {
            "address": [],  # liste d’adresses
            "senderAddress": sender_address,  # le même que dans l’URL
            "outboundSMSTextMessage": {"message": safe_text},
            "senderName": "SMIT"  # inutile ici : géré côté Orange si déjà approuvé
        }
    }

    for raw_number in recipients:
        number = str(raw_number).strip()
        if not number:
            continue

        payload = copy.deepcopy(payload_template)
        payload["outboundSMSMessageRequest"]["address"] = [f"tel:{number}"]

        try:
            resp = requests.post(sms_url, headers=headers, json=payload, timeout=20)
            if resp.status_code not in (200, 201):
                print(f"❌ Orange SMS API -> {resp.status_code} : {resp.text}")
                resp.raise_for_status()
            else:
                print(f"✅ SMS envoyé à {number} | Response: {resp.text}")
        except requests.RequestException as e:
            print(f"❌ Erreur SMS Orange vers {number} : {e}")

# def send_whatsapp(recipients, message):
#     """
#     Envoie des messages WhatsApp via Twilio
#     :param recipients: liste de numéros de téléphone au format international (ex : +2250700000000)
#     :param message: contenu du message (sera optimisé)
#     """
#     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#     message = optimize_sms_text(message)
#
#     for number in recipients:
#         whatsapp_number = f'whatsapp:{number}'
#         try:
#             client.messages.create(
#                 to=whatsapp_number,
#                 from_='whatsapp:+14155238886',  # Numéro Sandbox ou WhatsApp Twilio validé
#                 body=message
#             )
#         except Exception as e:
#             print(f"Erreur d'envoi WhatsApp à {number} : {str(e)}")
