# core/utils/phones.py
import re
import phonenumbers
from phonenumbers import PhoneNumberFormat

DEFAULT_REGION = "CI"  # Côte d'Ivoire

def normalize_phone(raw: str, region: str = DEFAULT_REGION) -> str:
    """
    Retourne un numéro au format E.164: +225XXXXXXXXXX
    Lève ValueError si invalide.
    """
    if not raw:
        raise ValueError("Téléphone vide")

    # nettoie (garde + et chiffres)
    cleaned = re.sub(r"[^\d+]", "", raw.strip())

    # convertit 00XXXX -> +XXXX
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]

    # parse
    try:
        num = phonenumbers.parse(cleaned, region)
    except phonenumbers.NumberParseException:
        raise ValueError("Téléphone invalide")

    if not phonenumbers.is_possible_number(num) or not phonenumbers.is_valid_number(num):
        raise ValueError("Téléphone invalide")

    return phonenumbers.format_number(num, PhoneNumberFormat.E164)


def mask_phone(e164: str) -> str:
    """
    Masque un E.164: +22507****7070
    """
    if not e164:
        return "-"
    # garde +225 + 2 premiers + 2 derniers
    if len(e164) <= 6:
        return e164
    return e164[:6] + "****" + e164[-2:]