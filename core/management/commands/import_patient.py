import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from core.models import Patient, Employee
from smit.models import Consultation

DEFAULT_PASSWORD = "password2smit24"


# Helper function to format phone numbers
def format_phone_number(contact):
    contact = str(contact)  # Ensure the contact is treated as a string
    if len(contact) == 8:  # If it's only 8 digits, add the appropriate prefix
        # Assume it's Orange CI, MTN CI, or MOOV CI
        if contact.startswith('07') or contact.startswith('08') or contact.startswith('09') or contact.startswith(
                '49') or contact.startswith('59'):  # Orange CI number patterns
            return '07' + contact
        elif contact.startswith('45') or contact.startswith('44') or contact.startswith('46') or contact.startswith(
                '05') or contact.startswith('06'):  # MTN CI number patterns
            return '05' + contact
        elif contact.startswith('01') or contact.startswith('02') or contact.startswith('03') or contact.startswith(
                '41') or contact.startswith('42'):  # MOOV CI number patterns
            return '01' + contact
    # If the contact is already 10 digits, return as is
    return contact


class Command(BaseCommand):
    help = 'Import patients data from Excel file and create consultations and doctors'

    def handle(self, *args, **kwargs):
        file_path = 'static/donnessmitpatients.xlsx'
        df = pd.read_excel(file_path, engine='openpyxl')

        for index, row in df.iterrows():
            nom = row.get('nom', 'Inconnu')
            prenom = row.get('prenom', 'Inconnu')
            contact = format_phone_number(row.get('contact', '00000000'))
            naissance_raw = row.get('date_naissance', None)
            date_naissance = None
            if pd.notnull(naissance_raw):
                try:
                    date_naissance = pd.to_datetime(naissance_raw).date()
                except Exception:
                    self.stdout.write(self.style.WARNING(f"⚠️ Date invalide pour {nom} {prenom}, ignorée."))
            sexe = row.get('sexe', 'Non précisé')
            nationalite = row.get('nationalite', 'Non précisé')
            profession = row.get('profession', 'Inconnue')
            code_vih = str(row.get('code_vih', '')).replace('/', '')
            motif_consultation = row.get('motif_consultation', 'Aucun motif')
            medecin_nom = row.get('medecin', 'Médecin inconnu')

            # Vérification des duplications
            if Patient.objects.filter(code_vih=code_vih).exists():
                self.stdout.write(self.style.WARNING(f"⚠️ Patient avec le code VIH {code_vih} déjà existant."))
                continue

            try:
                patient = Patient(
                    nom=nom,
                    prenoms=prenom,
                    date_naissance=date_naissance,
                    genre=sexe,
                    nationalite=nationalite,
                    profession=profession,
                    contact=contact,
                    code_vih=code_vih,
                    situation_matrimoniale='Célibataire',
                    created_at=timezone.now()
                )
                patient.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur lors de la création du patient {nom} {prenom} : {e}"))
                continue

            medecin_raw = row.get('medecin', '')
            medecin_nom = str(medecin_raw).strip() if pd.notnull(medecin_raw) else 'Médecin inconnu'

            username = medecin_nom.lower().replace(" ", ".")

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': medecin_nom.split()[0],
                    'last_name': medecin_nom.split()[1] if len(medecin_nom.split()) > 1 else '',
                    'email': f'{username}@hospital.com',
                }
            )
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()

            doctor, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'phone': '00000000',
                    'gender': 'Male' if sexe == 'Homme' else 'Female',
                    'created_at': timezone.now(),
                }
            )

            Consultation.objects.create(
                patient=patient,
                doctor=doctor,
                reason=motif_consultation,
                consultation_date=timezone.now(),
                status='Scheduled'
            )

        self.stdout.write(self.style.SUCCESS("✅ Importation terminée avec succès."))

# class Command(BaseCommand):
#     help = 'Import patients data from Excel file and create consultations and doctors'
#
#     def handle(self, *args, **kwargs):
#         # Load the Excel file
#         file_path = 'static/donnessmitpatients.xlsx'  # Update this path with your actual file path
#         df = pd.read_excel(file_path, engine='openpyxl')
#
#         for index, row in df.iterrows():
#             # Format the contact number
#             contact = row['contact'] if pd.notnull(row['contact']) else '00000000'
#             contact = format_phone_number(contact)
#
#             # Handle patient creation or update
#             nom = row['nom'] if pd.notnull(row['nom']) else 'Inconnu'
#             prenom = row['prenom'] if pd.notnull(row['prenom']) else 'Inconnu'
#             date_naissance = pd.to_datetime(row['date_naissance'], errors='coerce').date() if pd.notnull(
#                 row['date_naissance']) else None
#             sexe = row['sexe'] if pd.notnull(row['sexe']) else 'Non précisé'
#             nationalite = row['nationalite'] if pd.notnull(row['nationalite']) else 'Non précisé'
#             profession = row['profession'] if pd.notnull(row['profession']) else 'Inconnue'
#             code_vih = str(row['code_vih']).replace('/', '') if pd.notnull(row['code_vih']) else '0000'
#             motif_consultation = row['motif_consultation'] if pd.notnull(row['motif_consultation']) else 'Aucun motif'
#             medecin_nom = row['medecin'] if pd.notnull(row['medecin']) else 'Médecin inconnu'
#
#             # Check if a patient with the same code_vih already exists
#             if Patient.objects.filter(code_vih=code_vih).exists():
#                 self.stdout.write(self.style.WARNING(f"Patient with code VIH {code_vih} already exists, skipping..."))
#                 continue
#
#             # Create or update the patient
#             patient, created = Patient.objects.update_or_create(
#                 nom=nom,
#                 prenoms=prenom,
#                 defaults={
#                     'date_naissance': date_naissance,
#                     'genre': sexe,
#                     'nationalite': nationalite,
#                     'profession': profession,
#                     'contact': contact,  # Use the formatted contact
#                     'code_vih': code_vih,
#                     'situation_matrimoniale': 'Célibataire',  # Default value
#                     'created_at': timezone.now(),
#                 }
#             )
#
#             # Check if doctor exists, if not create user and employee
#             user, created = User.objects.get_or_create(
#                 username=medecin_nom.lower().replace(" ", "."),
#                 defaults={
#                     'first_name': medecin_nom.split()[0] if medecin_nom else '',
#                     'last_name': medecin_nom.split()[1] if len(medecin_nom.split()) > 1 else '',
#                     'email': f'{medecin_nom.lower().replace(" ", ".")}@hospital.com',
#                 }
#             )
#             if created:
#                 user.set_password(DEFAULT_PASSWORD)
#                 user.save()
#
#             # Create or update Employee (doctor)
#             doctor, created = Employee.objects.get_or_create(
#                 user=user,
#                 defaults={
#                     # 'job_title': 'Doctor',
#                     'phone': '00000000',  # Default phone number, adjust as needed
#                     'gender': 'Male' if sexe == 'Homme' else 'Female',
#                     'created_at': timezone.now(),
#                 }
#             )
#
#             # Create Consultation
#             consultation = Consultation.objects.create(
#                 patient=patient,
#                 doctor=doctor,
#                 reason=motif_consultation,
#                 consultation_date=timezone.now(),
#                 status='Scheduled'  # Default status
#             )
#
#         self.stdout.write(self.style.SUCCESS('Patients, consultations, and doctors imported successfully.'))
