import random
from datetime import timedelta

from django.core.management import BaseCommand
from faker import Faker

from core.models import Patient, ServiceSubActivity, Service, Employee, Maladie
from pharmacy.models import RendezVous, Molecule, Medicament
from smit.models import Suivi, Appointment, TraitementARV, InfectionOpportuniste, Comorbidite, Vaccination, Protocole, \
    TypeProtocole, Examen, EtapeProtocole


class Command(BaseCommand):
    help = "Generate fake data for Suivi and related models"

    def handle(self, *args, **kwargs):
        fake = Faker()
        self.stdout.write("Generating fake data...")

        # Generate fake TypeProtocole
        for _ in range(3):  # Create 3 types of protocoles
            type_protocole = TypeProtocole.objects.create(
                nom=fake.word(),
                description=fake.text(),
                parent=None  # You can set parent as another TypeProtocole for hierarchical types
            )
            self.stdout.write(f"Created TypeProtocole: {type_protocole.nom}")

        # Generate fake patients
        for _ in range(10):  # Number of patients to generate
            patient = Patient.objects.create(
                nom=fake.last_name(),
                prenoms=fake.first_name(),
                contact=fake.phone_number(),
                date_naissance=fake.date_of_birth(minimum_age=20, maximum_age=60),
                genre=random.choice(['M', 'F']),
                profession=fake.job(),
                status="positif"
            )

            self.stdout.write(f"Created Patient: {patient.nom} {patient.prenoms}")

            # Generate related Suivi
            for _ in range(3):  # Number of suivis per patient
                suivi = Suivi.objects.create(
                    patient=patient,
                    mode=random.choice(['permanent', 'occasionnel', 'periodique']),
                    activite=ServiceSubActivity.objects.order_by('?').first(),
                    services=Service.objects.order_by('?').first(),
                    rdvconsult=Appointment.objects.order_by('?').first(),
                    rdvpharmacie=None,
                    date_suivi=fake.date_this_year(),
                    statut_patient=random.choice(['actif', 'perdu_de_vue', 'transferé', 'décédé']),
                    adherence_traitement=random.choice(['bonne', 'moyenne', 'faible']),
                    poids=round(random.uniform(50.0, 90.0), 2),
                    cd4=random.randint(200, 1200),
                    charge_virale=random.randint(50, 50000),
                    observations=fake.text()
                )

                self.stdout.write(f"  Created Suivi for {suivi.patient.nom} {suivi.patient.prenoms}")

                # Generate Protocoles for the Suivi
                for _ in range(2):  # Create 2 protocoles per suivi
                    protocole = Protocole.objects.create(
                        nom=fake.word(),
                        description=fake.text(),
                        type_protocole=TypeProtocole.objects.order_by('?').first(),
                        duree=random.randint(30, 180),
                        date_debut=fake.date_this_year(),
                        patient=patient,
                        suivi=suivi,
                        maladies=Maladie.objects.order_by('?').first()
                    )
                    self.stdout.write(f"    Created Protocole: {protocole.nom}")

                    # Assign molecules and medications to the protocole
                    protocole.molecules.set(Molecule.objects.order_by('?')[:3])  # Assign up to 3 molecules
                    protocole.medicament.set(Medicament.objects.order_by('?')[:3])  # Assign up to 3 medications
                    protocole.rendezvous.set(Appointment.objects.order_by('?')[:2])  # Assign up to 2 appointments
                    protocole.examens.set(Examen.objects.order_by('?')[:2])  # Assign up to 2 exams

                    # Generate Etapes for the Protocole
                    for i in range(1, 4):  # Create 3 steps for each protocole
                        etape = EtapeProtocole.objects.create(
                            protocole=protocole,
                            nom=f"Étape {i} - {protocole.nom}",
                            description=fake.text(),
                            date_debut=fake.date_between(start_date=protocole.date_debut,
                                                         end_date=protocole.date_debut + timedelta(days=30)),
                            date_fin=fake.date_between(start_date=protocole.date_debut + timedelta(days=31),
                                                       end_date=protocole.date_debut + timedelta(days=60)),
                        )
                        self.stdout.write(f"      Created EtapeProtocole: {etape.nom}")

                # Generate related RendezVous
                for _ in range(2):  # Number of rendezvous per suivi
                    rdv = RendezVous.objects.create(
                        patient=patient,
                        pharmacie=None,
                        medicaments=None,
                        service=suivi.services,
                        doctor=Employee.objects.order_by('?').first(),
                        suivi=suivi,
                        date=fake.date_this_year(),
                        time=fake.time(),
                        reason=random.choice(["Récupération des médicaments", "Consultation médicale"]),
                        status=random.choice(['Scheduled', 'Completed', 'Missed']),
                        recurrence=random.choice(['None', 'Weekly', 'Monthly']),
                        recurrence_end_date=fake.date_this_year() if random.choice([True, False]) else None,
                        reminder_sent=random.choice([True, False]),
                        created_by=Employee.objects.order_by('?').first()
                    )
                    self.stdout.write(f"    Created RendezVous for {rdv.patient.nom} on {rdv.date}")

                # Generate related TraitementARV
                traitement = TraitementARV.objects.create(
                    suivi=suivi,
                    patient=patient,
                    nom=fake.word(),
                    description=fake.text(),
                    dosage=f"{random.randint(1, 3)} comprimé(s) par jour",
                    forme_pharmaceutique=random.choice(['comprimé', 'solution_orale', 'injectable']),
                    type_traitement=random.choice(['première_ligne', 'deuxième_ligne', 'troisième_ligne']),
                    duree_traitement=random.randint(6, 24),
                    posologie_details=fake.text(),
                    effet_secondaire_courant=fake.text(),
                    interaction_medicamenteuse=fake.text(),
                    efficacite=round(random.uniform(70.0, 99.9), 2)
                )
                self.stdout.write(f"    Created TraitementARV: {traitement.nom}")

                # Generate related InfectionOpportuniste
                for _ in range(2):
                    infection = InfectionOpportuniste.objects.create(
                        patient=patient,
                        suivi=suivi,
                        type_infection=fake.word(),
                        date_diagnostic=fake.date_this_year(),
                        gravite=random.choice(['faible', 'modérée', 'sévère']),
                        traitement=fake.text(),
                        statut_traitement=random.choice(['en cours', 'terminé', 'abandonné'])
                    )
                    self.stdout.write(f"      Created InfectionOpportuniste: {infection.type_infection}")

                # Generate related Comorbidite
                for _ in range(2):
                    comorbidite = Comorbidite.objects.create(
                        patient=patient,
                        suivi=suivi,
                        type_comorbidite=fake.word(),
                        date_diagnostic=fake.date_this_year(),
                        traitement=fake.text(),
                        statut_traitement=random.choice(['en cours', 'terminé', 'abandonné']),
                        impact_sur_vih=fake.text(),
                        recommandations=fake.text()
                    )
                    self.stdout.write(f"      Created Comorbidite: {comorbidite.type_comorbidite}")

                # Generate related Vaccination
                for _ in range(2):
                    vaccination = Vaccination.objects.create(
                        patient=patient,
                        type_vaccin=random.choice(['Hépatite B', 'Pneumocoque', 'Grippe', 'COVID-19']),
                        date_administration=fake.date_this_year(),
                        centre_vaccination=fake.company(),
                        lot_vaccin=fake.bothify('LOT###???'),
                        professionnel_sante=fake.name(),
                        rappel_necessaire=random.choice([True, False]),
                        date_rappel=fake.date_this_year() if random.choice([True, False]) else None,
                        effets_secondaires=fake.text(),
                        remarques=fake.text()
                    )
                    self.stdout.write(f"      Created Vaccination: {vaccination.type_vaccin}")

        self.stdout.write("Fake data generation completed!")
