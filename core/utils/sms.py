import os
import unicodedata

import requests
from twilio.rest import Client
from django.conf import settings


ORANGE_TOKEN_URL = "https://api.orange.com/oauth/v3/token"
ORANGE_SMS_URL = "https://api.orange.com/smsmessaging/v1/outbound/{}/requests"


def get_orange_sms_token():
    client_id = settings.ORANGE_SMS_CLIENT_ID
    client_secret = settings.ORANGE_SMS_CLIENT_SECRET

    print(client_id)
    print(client_secret)

    response = requests.post(
        ORANGE_TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    response.raise_for_status()
    return response.json()["access_token"]


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


def send_sms(recipients, message):
    access_token = get_orange_sms_token()
    sender_address = settings.ORANGE_SMS_SENDER  # ex: 'tel:+22507XXXXXXX'
    print(sender_address)
    sms_url = ORANGE_SMS_URL.format(sender_address)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload_template = {
        "outboundSMSMessageRequest": {
            "address": "",  # A remplir pour chaque destinataire
            "senderAddress": sender_address,
            "outboundSMSTextMessage": {
                "message": optimize_sms_text(message)
            }
        }
    }

    for number in recipients:
        # Format MSISDN pour Orange API
        recipient_address = f"tel:{number}"
        payload = payload_template.copy()
        payload["outboundSMSMessageRequest"]["address"] = recipient_address

        try:
            response = requests.post(sms_url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"✅ SMS envoyé à {number}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur SMS Orange vers {number} : {str(e)}")


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


def send_whatsapp(recipients, message):
    """
    Envoie des messages WhatsApp via Twilio
    :param recipients: liste de numéros de téléphone au format international (ex : +2250700000000)
    :param message: contenu du message (sera optimisé)
    """
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = optimize_sms_text(message)

    for number in recipients:
        whatsapp_number = f'whatsapp:{number}'
        try:
            client.messages.create(
                to=whatsapp_number,
                from_='whatsapp:+14155238886',  # Numéro Sandbox ou WhatsApp Twilio validé
                body=message
            )
        except Exception as e:
            print(f"Erreur d'envoi WhatsApp à {number} : {str(e)}")
