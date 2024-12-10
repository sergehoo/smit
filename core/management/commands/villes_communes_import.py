import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand

from core.models import Location


class Command(BaseCommand):
    help = 'Importe les villes et communes de Côte d\'Ivoire dans le modèle Location'

    def handle(self, *args, **kwargs):
        url = 'https://fr.wikipedia.org/wiki/Liste_des_communes_de_C%C3%B4te_d%27Ivoire'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Supposons que les noms des communes sont dans des balises <li> dans une section spécifique
        communes = []
        for li in soup.select('div.mw-parser-output ul li'):
            commune_name = li.get_text(strip=True)
            if commune_name:  # Vérifiez que le nom n'est pas vide
                communes.append(commune_name)

        # Insérer les communes dans la base de données
        for commune in communes:
            Location.objects.get_or_create(name=commune, defaults={'type': 'Commune'})
            self.stdout.write(self.style.SUCCESS(f'Commune "{commune}" importée avec succès.'))

        self.stdout.write(self.style.SUCCESS('Importation des communes terminée.'))