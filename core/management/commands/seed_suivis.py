from django.core.management.base import BaseCommand
from faker import Faker
import random

from core.models import Service, Patient
from smit.models import Suivi

fake = Faker()


class Command(BaseCommand):
    help = "Seed fake Suivi records for testing"

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Number of Suivi to create')

    def handle(self, *args, **kwargs):
        total = kwargs['total']

        patients = list(Patient.objects.all())
        services = list(Service.objects.all())

        if not patients:
            self.stdout.write(self.style.ERROR("Aucun patient disponible !"))
            return

        for _ in range(total):
            patient = random.choice(patients)
            service = random.choice(services) if services else None

            poids = round(random.uniform(40, 90), 1)
            cd4 = random.randint(50, 800)
            charge_virale = random.randint(50, 200000)

            suivi = Suivi.objects.create(
                patient=patient,
                services=service,
                date_suivi=fake.date_this_year(),
                poids=poids,
                cd4=cd4,
                charge_virale=charge_virale,
                stade_oms=random.choice([1, 2, 3, 4]),
                presence_io=random.choice([True, False]),
                adherence_traitement=random.choice(['bonne', 'moyenne', 'faible']),
                observations=fake.paragraph(nb_sentences=3),
                effets_secondaires=fake.sentence(),
                prophylaxie_cotrimoxazole=random.choice([True, False]),
                difficultes_psychosociales=fake.paragraph(),
                soutien_familial=random.choice(['bon', 'modere', 'faible', 'absent']),
                mode=random.choice(['permanent', 'occasionnel', 'periodique']),
            )

            suivi.generate_auto_recommandations()
            suivi.save()

        self.stdout.write(self.style.SUCCESS(f"{total} Suivi créés avec succès 🚀"))
