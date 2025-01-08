from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import datetime, timedelta

from core.models import Employee, Service, ServiceSubActivity, Patient
from pharmacy.models import Medicament
from smit.models import Hospitalization, Constante, Prescription, SigneFonctionnel, IndicateurBiologique, \
    IndicateurFonctionnel, IndicateurSubjectif, Consultation, Appointment

fake = Faker()


class Command(BaseCommand):
    help = 'Generate fake data for Patient and related models'

    def handle(self, *args, **kwargs):
        self.generate_patients(100)

    def generate_patients(self, count):
        employees = Employee.objects.all()
        services = ServiceSubActivity.objects.all()

        if not employees.exists() or not services.exists():
            print("Erreur : Aucun employé ou service existant trouvé. Veuillez d'abord ajouter des employés et services.")
            return

        for _ in range(count):
            # Créer un patient avec des informations fictives
            patient = Patient.objects.create(
                code_patient=fake.unique.bothify(text='??######'),
                code_vih=fake.unique.bothify(text='??######'),
                nom=fake.last_name(),
                prenoms=fake.first_name(),
                contact=fake.phone_number(),
                situation_matrimoniale=random.choice(['Célibataire', 'Marié', 'Divorcé']),
                lieu_naissance=fake.city(),
                date_naissance=fake.date_of_birth(minimum_age=18, maximum_age=90),
                genre=random.choice(['HOMME', 'FEMME']),
                nationalite=fake.country(),
                profession=fake.job(),
                groupe_sanguin=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                created_by=random.choice(employees)
            )

            selected_employee = random.choice(employees)
            hospitalization = Hospitalization.objects.create(
                patient=patient,
                activite=random.choice(services),
                doctor=selected_employee.user,
                admission_date=fake.date_time_this_year(),
                discharge_date=fake.date_time_this_year() if random.choice([True, False]) else None,
                reason_for_admission=fake.sentence(nb_words=6),
                status=random.choice(['En cours', 'Sorti', 'Décédé']),
                room=fake.building_number()
            )

            # Créer des consultations pour le patient
            for _ in range(30):  # Exemple : 5 consultations par patient
                Consultation.objects.create(
                    numeros=fake.unique.bothify(text='CONS-######'),
                    activite=random.choice(services),
                    patient=patient,
                    doctor=selected_employee,
                    consultation_date=fake.date_time_this_year(),
                    reason=fake.sentence(nb_words=8),
                    diagnosis=fake.paragraph(nb_sentences=2),
                    commentaires=fake.paragraph(nb_sentences=2),
                    status=random.choice(['Scheduled', 'Completed', 'Cancelled']),
                    hospitalised=random.choice([0, 1]),
                    created_by=selected_employee
                )

            # Créer des rendez-vous pour le patient
            for _ in range(30):  # Exemple : 3 rendez-vous par patient
                Appointment.objects.create(
                    patient=patient,
                    service=random.choice(Service.objects.all()),
                    doctor=selected_employee,
                    date=fake.date_this_year(),
                    time=fake.time(),
                    reason=fake.sentence(nb_words=6),
                    status=random.choice(['Scheduled', 'Completed', 'Cancelled']),
                    created_by=selected_employee
                )

            print(f"Patient {patient.nom} créé avec consultations et rendez-vous.")
        print(f"{count} patients créés avec consultations, rendez-vous, hospitalisations et dossiers connexes.")
