import pandas as pd
from django.contrib.auth.models import User
from django.core.management import BaseCommand

from core.models import Employee


class Command(BaseCommand):
    help = "Importer des employés et utilisateurs à partir d'un fichier Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help="Chemin vers le fichier Excel contenant les employés",
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        try:
            # Lire le fichier Excel
            df = pd.read_excel(file_path)

            # Vérification des colonnes nécessaires
            required_columns = ["NOM& PRENOMS", "FONCTIONS", "ADRESSE-EMAIL"]
            if not all(col in df.columns for col in required_columns):
                self.stdout.write(
                    self.style.ERROR("Le fichier doit contenir les colonnes: NOM& PRENOMS, FONCTIONS, ADRESSE-EMAIL"))
                return

            # Parcourir les lignes du fichier
            for index, row in df.iterrows():
                full_name = row["NOM& PRENOMS"].strip()
                job_title = row["FONCTIONS"].strip()
                email = row["ADRESSE-EMAIL"].strip()

                # Découper NOM& PRENOMS
                names = full_name.split()
                if len(names) < 2:
                    self.stdout.write(
                        self.style.WARNING(f"Nom complet invalide pour la ligne {index + 2}: {full_name}"))
                    continue

                last_name = names[0]
                first_name = " ".join(names[1:])

                # Vérifier si l'utilisateur existe déjà
                user, created_user = User.objects.get_or_create(
                    username=email,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'is_active': True,
                    }
                )

                if created_user:
                    user.set_password("password2smit24")
                    user.save()

                # Créer ou mettre à jour l'employé
                employee, created_employee = Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        'job_title': job_title,
                        'personal_mail': email,
                    }
                )

                if created_employee:
                    self.stdout.write(self.style.SUCCESS(f"Employé ajouté: {full_name} ({email})"))
                else:
                    self.stdout.write(self.style.WARNING(f"L'employé existe déjà: {full_name} ({email})"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'importation: {e}"))