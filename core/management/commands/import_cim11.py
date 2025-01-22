import requests
from django.core.management.base import BaseCommand

from core.models import Maladie


class Command(BaseCommand):
    help = "Importe les entités CIM-11 en français depuis l'API OMS dans la base de données."

    # Informations d'authentification
    TOKEN_ENDPOINT = 'https://icdaccessmanagement.who.int/connect/token'
    CLIENT_ID = '9b40ae71-7b78-4341-8412-1f888d46c239_909e4c74-0652-4158-a3df-cace68f2ce05'
    CLIENT_SECRET = 'AOjYnlYDA5y9fuGQNctk0jD52YH3/0cRtWSU07V0uPI='
    SCOPE = 'icdapi_access'
    GRANT_TYPE = 'client_credentials'
    API_URI = 'https://id.who.int/icd/entity'

    def get_access_token(self):
        payload = {
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'scope': self.SCOPE,
            'grant_type': self.GRANT_TYPE,
        }
        try:
            response = requests.post(self.TOKEN_ENDPOINT, data=payload, verify=True)
            response.raise_for_status()
            token = response.json().get('access_token')
            if not token:
                self.stderr.write("Erreur : Le jeton d'accès n'a pas été retourné.")
            return token
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Erreur lors de l'obtention du jeton : {e}")
            return None

    def fetch_cim11_entities(self, token):
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Accept-Language': 'fr',  # Langue française
            'API-Version': 'v2',
        }
        try:
            response = requests.get(self.API_URI, headers=headers, verify=True)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Erreur lors de la récupération des entités CIM-11 : {e}")
            return None

    def fetch_entity_details(self, url, token):
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Accept-Language': 'fr',  # Langue française
            'API-Version': 'v2',
        }
        try:
            response = requests.get(url, headers=headers, verify=True)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Erreur lors de la récupération des détails de l'entité : {e}")
            return None

    def process_entity(self, url, token, processed_urls):
        if url in processed_urls:
            return  # Éviter les doublons
        processed_urls.add(url)

        entity_details = self.fetch_entity_details(url, token)
        if not entity_details:
            self.stderr.write(f"Échec de récupération pour l'URL : {url}")
            return

        # Extraire uniquement le code et l'URL complète
        code = url.split('/')[-1]  # Obtenir uniquement la partie finale de l'URL comme code
        urlcim = url
        title = entity_details.get('title', {}).get('@value', 'Titre non disponible')
        definition = entity_details.get('definition', {}).get('@value', '')

        try:
            Maladie.objects.get_or_create(
                code_cim=code,
                defaults={
                    "nom": title,
                    "description": definition,
                    "categorie": "autre",
                    "urlcim": urlcim,
                },
            )
            self.stdout.write(f"Maladie enregistrée : {title} ({code})")
        except Exception as e:
            self.stderr.write(f"Erreur lors de l'enregistrement de l'entité {code} : {e}")
            return

        for child_url in entity_details.get('child', []):
            self.process_entity(child_url, token, processed_urls)

    def handle(self, *args, **kwargs):
        self.stdout.write("Début de l'importation des entités CIM-11...")

        token = self.get_access_token()
        if not token:
            self.stderr.write("Échec de l'obtention du jeton d'accès.")
            return

        entities = self.fetch_cim11_entities(token)
        if not entities:
            self.stderr.write("Aucune entité récupérée depuis l'API.")
            return

        child_urls = entities.get('child', [])
        if not child_urls:
            self.stderr.write("Aucune URL d'entité enfant trouvée.")
            return

        processed_urls = set()

        for url in child_urls:
            self.process_entity(url, token, processed_urls)

        self.stdout.write(
            self.style.SUCCESS(f"{len(processed_urls)} maladies ont été enregistrées avec succès.")
        )
