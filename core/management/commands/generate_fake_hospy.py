from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import datetime, timedelta

from core.models import Employee, Service, ServiceSubActivity, Patient
from pharmacy.models import Medicament
from smit.models import Hospitalization, Constante, Prescription, SigneFonctionnel, IndicateurBiologique, \
    IndicateurFonctionnel, IndicateurSubjectif

fake = Faker()


class Command(BaseCommand):
    help = 'Generate fake data for Patient and related models'

    def handle(self, *args, **kwargs):
        self.generate_patients(10)

    def generate_patients(self, count):
        # Utiliser les employés et services existants
        employees = Employee.objects.all()
        services = ServiceSubActivity.objects.all()

        if not employees.exists() or not services.exists():
            print(
                "Erreur : Aucun employé ou service existant trouvé. Veuillez d'abord ajouter des employés et services.")
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

            # Créer une hospitalisation pour le patient
        selected_employee = random.choice(employees)
        doctor_user = selected_employee.user
        hospitalization = Hospitalization.objects.create(
            patient=patient,
            activite=random.choice(services),
            doctor=doctor_user,  # Assigner l'utilisateur du médecin
            admission_date=fake.date_time_this_year(),
            discharge_date=fake.date_time_this_year() if random.choice([True, False]) else None,
            reason_for_admission=fake.sentence(nb_words=6),
            status=random.choice(['En cours', 'Sorti', 'Décédé']),
            room=fake.building_number()
        )

        # Créer des constantes vitales pour le patient
        for _ in range(10):
            Constante.objects.create(
                patient=patient,
                hospitalisation=hospitalization,
                tension_systolique=random.randint(90, 140),
                tension_diastolique=random.randint(60, 90),
                frequence_cardiaque=random.randint(60, 100),
                frequence_respiratoire=random.randint(12, 20),
                temperature=random.uniform(36, 40),
                saturation_oxygene=random.randint(95, 100),
                glycemie=random.uniform(0.7, 1.2),
                poids=random.uniform(50, 100),
                taille=random.uniform(150, 200),
                pouls=random.randint(60, 100),
                created_by=random.choice(employees)
            )

            # Créer des prescriptions pour le patient
            for _ in range(10):
                Prescription.objects.create(
                    patient=patient,
                    doctor=random.choice(employees),
                    medication=Medicament.objects.create(nom=fake.word()),
                    quantity=random.randint(1, 5),
                    status=random.choice(['Pending', 'Dispensed', 'Cancelled']),
                    created_by=random.choice(employees)
                )

            # Créer des indicateurs fonctionnels, biologiques et subjectifs
            SigneFonctionnel.objects.create(
                nom=fake.word(),
                valeure=random.choice(['oui', 'non']),
                hospitalisation=hospitalization
            )

            IndicateurBiologique.objects.create(
                hospitalisation=hospitalization,
                globules_blancs=random.uniform(4, 11),
                hemoglobine=random.uniform(12, 17),
                plaquettes=random.randint(150, 450),
                crp=random.uniform(0, 5),
                glucose_sanguin=random.uniform(0.7, 1.2),
                date=fake.date_this_year()
            )

            IndicateurFonctionnel.objects.create(
                hospitalisation=hospitalization,
                mobilite=random.choice(['indépendant', 'assisté', 'immobile']),
                conscience=random.choice(['alerte', 'somnolent', 'inconscient']),
                debit_urinaire=random.uniform(0.5, 2.0),
                date=fake.date_this_year()
            )

            IndicateurSubjectif.objects.create(
                hospitalisation=hospitalization,
                bien_etre=random.randint(0, 10),
                date=fake.date_this_year()
            )

        print(f"{count} patients created with related hospitalizations and records")
