# Charger le fichier GeoJSON
import json

# from django.contrib.gis.gdal import Point
from django.core.management import BaseCommand

from core.models import Localite

file_path = '/Users/ogahserge/Documents/smitci/static/geoBoundaries-CIV-ADM3.geojson'

with open(file_path, 'r') as geojson_file:
    geo_data = json.load(geojson_file)

# Boucler sur les données et insérer dans la base de données
for feature in geo_data['features']:
    nom = feature['properties'].get('shapeName', None)
    type_localite = feature['properties'].get('type', None)  # Si le fichier a un champ de type
    region = feature['properties'].get('region', None)  # Ajuster si nécessaire
    code = feature['properties'].get('code', None)  # Ajuster si nécessaire

    if nom:
        Localite.objects.create(nom=nom, code=code, type=type_localite, region=region)


# class Command(BaseCommand):
#     help = 'Importe les données GeoJSON dans Localite'
#
#     def add_arguments(self, parser):
#         parser.add_argument('geojson_file', type=str, help='Le chemin vers le fichier GeoJSON')
#
#     def handle(self, *args, **kwargs):
#         geojson_file = kwargs['geojson_file']
#
#         with open(geojson_file, 'r') as f:
#             data = json.load(f)
#
#             for feature in data['features']:
#                 properties = feature['properties']
#                 geometry = feature['geometry']
#
#                 nom = properties.get('name')
#                 code = properties.get('code')  # Assurez-vous que le fichier GeoJSON contient ce champ
#                 type_localite = properties.get('type')
#                 region = properties.get('region')  # Assurez-vous que le fichier GeoJSON contient ce champ
#                 geojson_data = json.dumps(feature)  # Si vous souhaitez sauvegarder l'intégralité de l'objet GeoJSON
#
#                 if geometry['type'] == 'Point':
#                     coordinates = geometry['coordinates']
#                     point = Point(coordinates[0], coordinates[1], srid=4326)
#
#                     Localite.objects.create(
#                         nom=nom,
#                         code=code,
#                         type=type_localite,
#                         region=region,
#                         geojson=geojson_data
#                     )
#
#         self.stdout.write(self.style.SUCCESS('Données GeoJSON importées avec succès dans Localite!'))
