import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point


class Command(BaseCommand):
    help = 'Importe les données GeoJSON dans Commune'

    def add_arguments(self, parser):
        parser.add_argument('geojson_file', type=str, help='Le chemin vers le fichier GeoJSON')

    def handle(self, *args, **kwargs):
        geojson_file = kwargs['geojson_file']

        with open(geojson_file, 'r') as f:
            data = json.load(f)

            for feature in data['features']:
                properties = feature['properties']
                geometry = feature['geometry']

                name = properties.get('name')
                name_en = properties.get('name:en')
                place = properties.get('place')
                population = properties.get('population')
                is_in = properties.get('is_in')
                source = properties.get('source')
                osm_id = properties.get('osm_id')
                osm_type = properties.get('osm_type')

                # Assurez-vous d'avoir une logique pour relier à la ville
                ville = City.objects.first()  # Ceci est un exemple, ajustez en fonction de votre logique

                if geometry['type'] == 'Point':
                    coordinates = geometry['coordinates']
                    point = Point(coordinates[0], coordinates[1], srid=4326)

                    Commune.objects.create(
                        # ville=ville,
                        name=name,
                        name_en=name_en,
                        place=place,
                        population=population,
                        is_in=is_in,
                        source=source,
                        osm_id=osm_id,
                        osm_type=osm_type,
                        geom=point
                    )

        self.stdout.write(self.style.SUCCESS('Données GeoJSON importées avec succès!'))