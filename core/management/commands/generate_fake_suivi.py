import random

from django.core.management import BaseCommand

from core.models import Patient, Employee, Service, ServiceSubActivity
from pharmacy.models import RendezVous
from smit.models import TraitementARV, Appointment, FicheSuiviClinique, Suivi
from faker import Faker

fake = Faker()


class Command(BaseCommand):
    help = "Generate fake data for Suivi and FicheSuiviClinique models"

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating fake data...")

        # Generate Patients
        patients = Patient.objects.all()
        if not patients.exists():
            self.stdout.write("No patients found. Add patients before generating data.")
            return

        # Generate Employees (Doctors)
        employees = Employee.objects.all()
        if not employees.exists():
            self.stdout.write("No employees found. Add employees before generating data.")
            return

        # Generate Services
        services = Service.objects.all()
        if not services.exists():
            self.stdout.write("No services found. Add services before generating data.")
            return

        # Generate ServiceSubActivity
        activities = ServiceSubActivity.objects.all()
        if not activities.exists():
            self.stdout.write("No sub-activities found. Add sub-activities before generating data.")
            return


        # Generate ARV treatments
        treatments = TraitementARV.objects.all()
        # if not treatments.exists():
        #     self.stdout.write("No ARV treatments found. Add ARV treatments before generating data.")
        #     return
        # Ajouter avant la génération des FicheSuiviClinique
        if not treatments.exists():
            self.stdout.write("No ARV treatments found. Generating some ARV treatments...")
            for _ in range(10):  # Générer 10 traitements ARV
                TraitementARV.objects.create(
                    nom=fake.word().capitalize(),
                    description=fake.text(max_nb_chars=100),
                    dosage=f"{random.randint(1, 3)}x par jour",
                    forme_pharmaceutique=random.choice(['comprimé', 'solution_orale', 'injectable']),
                    type_traitement=random.choice(['première_ligne', 'deuxième_ligne', 'troisième_ligne']),
                    duree_traitement=random.randint(6, 24),
                    posologie_details=fake.text(max_nb_chars=200),
                    effet_secondaire_courant=fake.text(max_nb_chars=150),
                    interaction_medicamenteuse=fake.text(max_nb_chars=150),
                    efficacite=round(random.uniform(85.0, 99.9), 2),
                )
            treatments = TraitementARV.objects.all()
            self.stdout.write("ARV treatments created.")

        # Generate Appointments and RendezVous
        appointments = Appointment.objects.all()
        rendezvous = RendezVous.objects.all()

        # Generate FicheSuiviClinique
        for _ in range(20):  # Number of consultations to generate
            patient = random.choice(patients)
            medecin = random.choice(employees)

            fiche = FicheSuiviClinique.objects.create(
                patient=patient,
                medecin=medecin,
                date_consultation=fake.date_between(start_date='-1y', end_date='today'),
                heure_consultation=fake.time(),
                observations_cliniques=fake.text(max_nb_chars=200),
                poids=round(random.uniform(50.0, 100.0), 2),
                taille=round(random.uniform(150.0, 200.0), 2),
                pression_arterielle=f"{random.randint(100, 140)}/{random.randint(60, 90)} mmHg",
                temperature=round(random.uniform(36.0, 38.5), 1),
                recommandations=fake.text(max_nb_chars=200),
                prochaine_consultation=fake.date_between(start_date='today', end_date='+1y'),
            )

            self.stdout.write(f"Created FicheSuiviClinique for patient {patient} on {fiche.date_consultation}")

            # Generate Suivi
            suivi = Suivi.objects.create(
                activite=random.choice(activities),
                services=random.choice(services),
                patient=patient,
                fichesuivie=fiche,
                traitement=random.choice(treatments),
                rdvconsult=random.choice(appointments) if appointments.exists() else None,
                rdvpharmacie=random.choice(rendezvous) if rendezvous.exists() else None,
                date_suivi=fake.date_between(start_date=fiche.date_consultation, end_date='today'),
                statut_patient=random.choice(['actif', 'perdu_de_vue', 'transferé', 'décédé']),
                adherence_traitement=random.choice(['bonne', 'moyenne', 'faible']),
                poids=round(random.uniform(50.0, 100.0), 2),
                cd4=random.randint(200, 1200),
                charge_virale=random.randint(50, 200000),
                observations=fake.text(max_nb_chars=200),
            )

            self.stdout.write(f"Created Suivi for patient {patient} on {suivi.date_suivi}")

        self.stdout.write("Fake data generation completed.")