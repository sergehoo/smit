import re
import uuid
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import FieldDoesNotExist

from core.models import Patient, Employee
from smit.models import Consultation

DEFAULT_PASSWORD = "password2smit24"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
def fit_field(model_cls, field_name, value, logger=None, who=""):
    """
    Tronque value selon max_length du champ (si CharField).
    - model_cls: classe du modèle (ex: Patient)
    - field_name: nom du champ (ex: 'nom')
    - value: valeur à insérer
    - logger: self.stdout.write (optionnel) pour log
    - who: identifiant lisible (ex: nom complet du patient) pour logs
    """
    if value is None:
        return None
    s = str(value)
    try:
        f = model_cls._meta.get_field(field_name)
    except Exception:
        return s  # champ inconnu -> ne rien faire

    if isinstance(f, models.CharField) and f.max_length:
        max_len = f.max_length
        if len(s) > max_len:
            if logger:
                logger(f"✂️  {who}: champ {model_cls.__name__}.{field_name} "
                       f"trop long ({len(s)}>{max_len}), tronqué.")
            return s[:max_len]
    return s
def is_nan(x):
    try:
        return pd.isna(x)
    except Exception:
        return False

def norm_str(val, upper=False):
    if is_nan(val) or val is None:
        return ""
    s = str(val).strip()
    return s.upper() if upper else s

def parse_date(val):
    if is_nan(val) or val in ("", None):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None

def clean_email(val):
    if is_nan(val) or val is None:
        return None
    s = str(val).strip().lower()
    if not s or s == "nan":
        return None
    return s if EMAIL_RE.match(s) else None

def normalize_ci_phone(raw: str):
    if raw is None:
        return ""
    s = "".join(ch for ch in str(raw) if ch.isdigit())
    if s.startswith("00225"): s = s[5:]
    elif s.startswith("225") and len(s) > 10: s = s[3:]
    elif s.startswith("0") and len(s) > 10: s = s[-10:]
    if len(s) == 10: return s
    if len(s) == 8:
        if s[:2] in {"07","08","09","49","59"}: return "07"+s
        if s[:2] in {"05","06","44","45","46"}: return "05"+s
        if s[:2] in {"01","02","03","41","42"}: return "01"+s
        return s
    return s

def unique_username(base: str) -> str:
    base = base.lower().replace(" ", ".").replace("..", ".") or "medecin"
    uname = base
    i = 1
    while User.objects.filter(username=uname).exists():
        i += 1
        uname = f"{base}.{i}"
    return uname

def patient_email_nullable() -> bool:
    try:
        f = Patient._meta.get_field("adresse_mail")
        return getattr(f, "null", False)
    except FieldDoesNotExist:
        return True  # par prudence

def build_placeholder_email(nom, prenoms, code_vih=None):
    slug_nom = re.sub(r"[^a-z0-9]+", "-", (nom or "").lower()).strip("-")
    slug_pre = re.sub(r"[^a-z0-9]+", "-", (prenoms or "").lower()).strip("-")
    tag = code_vih or uuid.uuid4().hex[:10]
    return f"no-mail+{slug_nom}.{slug_pre}.{tag}@example.com"

class Command(BaseCommand):
    help = "Importe les patients depuis Excel et crée consultations & médecins."

    def handle(self, *args, **kwargs):
        df = pd.read_excel("static/donnessmitpatients.xlsx", engine="openpyxl")
        mail_nullable = patient_email_nullable()

        for _, row in df.iterrows():
            nom = norm_str(row.get("nom"), upper=True) or "INCONNU"
            prenom = norm_str(row.get("prenom")) or "Inconnu"
            contact = normalize_ci_phone(row.get("contact"))
            date_naissance = parse_date(row.get("date_naissance"))
            sexe = norm_str(row.get("sexe")) or "Non précisé"
            nationalite = norm_str(row.get("nationalite")) or "Non précisée"
            profession = norm_str(row.get("profession")) or "Inconnue"

            raw_code_vih = row.get("code_vih", "")
            code_vih = None
            if not is_nan(raw_code_vih):
                tmp = norm_str(str(raw_code_vih).replace("/", ""))
                code_vih = tmp if tmp and tmp.lower() != "nan" else None

            # email (colonne 'adresse_mail' ou 'email' selon ton Excel)
            email = clean_email(row.get("adresse_mail", row.get("email")))
            if not email and not mail_nullable:
                email = build_placeholder_email(nom, prenom, code_vih)

            motif_consultation = norm_str(row.get("motif_consultation")) or "Aucun motif"
            medecin_nom = norm_str(row.get("medecin")) or "Médecin Inconnu"

            # Déduplication
            if code_vih and Patient.objects.filter(code_vih=code_vih).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Doublon code VIH, ignoré: {nom} {prenom}"))
                continue
            q = Q(nom=nom, prenoms=prenom)
            if date_naissance: q &= Q(date_naissance=date_naissance)
            if contact: q &= Q(contact=contact)
            if Patient.objects.filter(q).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Doublon naturel, ignoré: {nom} {prenom}"))
                continue

            try:
                with transaction.atomic():
                    patient_kwargs = dict(
                        nom=nom,
                        prenoms=prenom,
                        date_naissance=date_naissance,
                        genre=sexe,
                        nationalite=nationalite,
                        profession=profession,
                        contact=contact,
                        code_vih=code_vih,
                        situation_matrimoniale="Célibataire",
                        created_at=timezone.now(),
                    )
                    if email is not None:
                        patient_kwargs["adresse_mail"] = email
                    who = f"{nom} {prenom}".strip()
                    patient = Patient.objects.create(**patient_kwargs)

                    username = unique_username(medecin_nom.replace(" ", "."))
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "first_name": medecin_nom.split()[0] if medecin_nom else "",
                            "last_name": " ".join(medecin_nom.split()[1:]) if len(medecin_nom.split()) > 1 else "",
                            "email": f"{username}@hospital.com",
                        },
                    )
                    if created:
                        user.set_password(DEFAULT_PASSWORD)
                        user.save()

                    doctor, _ = Employee.objects.get_or_create(
                        user=user,
                        defaults={"phone": "", "gender": "Unknown", "created_at": timezone.now()},
                    )

                    Consultation.objects.create(
                        patient=patient,
                        doctor=doctor,
                        reason=motif_consultation,
                        consultation_date=timezone.now(),
                        status="Scheduled",
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur création patient {nom} {prenom} : {e}"))
                continue

        self.stdout.write(self.style.SUCCESS("✅ Importation terminée avec succès."))

# import pandas as pd
# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.contrib.auth.models import User
#
# from core.models import Patient, Employee
# from smit.models import Consultation
#
# DEFAULT_PASSWORD = "password2smit24"
#
#
# # Helper function to format phone numbers
# def format_phone_number(contact):
#     contact = str(contact)  # Ensure the contact is treated as a string
#     if len(contact) == 8:  # If it's only 8 digits, add the appropriate prefix
#         # Assume it's Orange CI, MTN CI, or MOOV CI
#         if contact.startswith('07') or contact.startswith('08') or contact.startswith('09') or contact.startswith(
#                 '49') or contact.startswith('59'):  # Orange CI number patterns
#             return '07' + contact
#         elif contact.startswith('45') or contact.startswith('44') or contact.startswith('46') or contact.startswith(
#                 '05') or contact.startswith('06'):  # MTN CI number patterns
#             return '05' + contact
#         elif contact.startswith('01') or contact.startswith('02') or contact.startswith('03') or contact.startswith(
#                 '41') or contact.startswith('42'):  # MOOV CI number patterns
#             return '01' + contact
#     # If the contact is already 10 digits, return as is
#     return contact
#
#
# class Command(BaseCommand):
#     help = 'Import patients data from Excel file and create consultations and doctors'
#
#     def handle(self, *args, **kwargs):
#         file_path = 'static/donnessmitpatients.xlsx'
#         df = pd.read_excel(file_path, engine='openpyxl')
#
#         for index, row in df.iterrows():
#             nom = row.get('nom', 'Inconnu')
#             prenom = row.get('prenom', 'Inconnu')
#             contact = format_phone_number(row.get('contact', '00000000'))
#             naissance_raw = row.get('date_naissance', None)
#             date_naissance = None
#             if pd.notnull(naissance_raw):
#                 try:
#                     date_naissance = pd.to_datetime(naissance_raw).date()
#                 except Exception:
#                     self.stdout.write(self.style.WARNING(f"⚠️ Date invalide pour {nom} {prenom}, ignorée."))
#             sexe = row.get('sexe', 'Non précisé')
#             nationalite = row.get('nationalite', 'Non précisé')
#             profession = row.get('profession', 'Inconnue')
#             code_vih = str(row.get('code_vih', '')).replace('/', '')
#             motif_consultation = row.get('motif_consultation', 'Aucun motif')
#             medecin_nom = row.get('medecin', 'Médecin inconnu')
#
#             # Vérification des duplications
#             if Patient.objects.filter(code_vih=code_vih).exists():
#                 self.stdout.write(self.style.WARNING(f"⚠️ Patient avec le code VIH {code_vih} déjà existant."))
#                 continue
#
#             try:
#                 patient = Patient(
#                     nom=nom,
#                     prenoms=prenom,
#                     date_naissance=date_naissance,
#                     genre=sexe,
#                     nationalite=nationalite,
#                     profession=profession,
#                     contact=contact,
#                     code_vih=code_vih,
#                     situation_matrimoniale='Célibataire',
#                     created_at=timezone.now()
#                 )
#                 patient.save()
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"❌ Erreur lors de la création du patient {nom} {prenom} : {e}"))
#                 continue
#
#             medecin_raw = row.get('medecin', '')
#             medecin_nom = str(medecin_raw).strip() if pd.notnull(medecin_raw) else 'Médecin inconnu'
#
#             username = medecin_nom.lower().replace(" ", ".")
#
#             user, created = User.objects.get_or_create(
#                 username=username,
#                 defaults={
#                     'first_name': medecin_nom.split()[0],
#                     'last_name': medecin_nom.split()[1] if len(medecin_nom.split()) > 1 else '',
#                     'email': f'{username}@hospital.com',
#                 }
#             )
#             if created:
#                 user.set_password(DEFAULT_PASSWORD)
#                 user.save()
#
#             doctor, _ = Employee.objects.get_or_create(
#                 user=user,
#                 defaults={
#                     'phone': '00000000',
#                     'gender': 'Male' if sexe == 'Homme' else 'Female',
#                     'created_at': timezone.now(),
#                 }
#             )
#
#             Consultation.objects.create(
#                 patient=patient,
#                 doctor=doctor,
#                 reason=motif_consultation,
#                 consultation_date=timezone.now(),
#                 status='Scheduled'
#             )
#
#         self.stdout.write(self.style.SUCCESS("✅ Importation terminée avec succès."))
