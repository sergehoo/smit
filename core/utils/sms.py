import unicodedata

from twilio.rest import Client
from django.conf import settings


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
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    for number in recipients:
        try:
            client.messages.create(
                messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
                body=message,
                # from_=settings.TWILIO_PHONE_NUMBER,
                to=number
            )
        except Exception as e:
            print(f"Erreur d'envoi du SMS à {number}: {str(e)}")


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
