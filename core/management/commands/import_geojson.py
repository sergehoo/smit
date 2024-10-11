import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from epidemie.models import DistrictSanitaire, ServiceSanitaire


class Command(BaseCommand):
    help = 'Importe les données GeoJSON dans ServiceSanitaire'

    def add_arguments(self, parser):
        parser.add_argument('geojson_file', type=str, help='Le chemin vers le fichier GeoJSON')

    def handle(self, *args, **kwargs):
        geojson_file = kwargs['geojson_file']

        with open(geojson_file, 'r') as f:
            data = json.load(f)

            for feature in data['features']:
                properties = feature['properties']
                geometry = feature['geometry']

                nom = properties.get('name')
                type = properties.get('type')
                district_id = properties.get('district_id')
                upstream = properties.get('upstream')
                date_modified = properties.get('date_modified')
                source_url = properties.get('source_url')
                completeness = properties.get('completeness')
                uuid = properties.get('uuid')
                source = properties.get('source')
                what3words = properties.get('what3words')
                version = properties.get('version')

                # Assurer que le district existe
                district = DistrictSanitaire.objects.filter(id=district_id).first()

                if geometry['type'] == 'Point':
                    coordinates = geometry['coordinates']
                    point = Point(coordinates[0], coordinates[1], srid=4326)

                    ServiceSanitaire.objects.create(
                        nom=nom,
                        type=type,
                        district=district,
                        geom=point,
                        upstream=upstream,
                        date_modified=date_modified,
                        source_url=source_url,
                        completeness=completeness,
                        uuid=uuid,
                        source=source,
                        what3words=what3words,
                        version=version
                    )

        self.stdout.write(self.style.SUCCESS('Données GeoJSON importées avec succès!'))