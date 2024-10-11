import os
from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon
from epidemie.models import HealthRegion, City


class Command(BaseCommand):
    help = 'Import GeoPackage data into Django models'

    def handle(self, *args, **options):
        gpkg_path = 'static/gadm41_CIV.gpkg'

        if not os.path.exists(gpkg_path):
            self.stdout.write(self.style.ERROR('GeoPackage file does not exist at the specified path'))
            return

        ds = DataSource(gpkg_path)

        # Import HealthRegions (ADM_ADM_1)
        layer = ds['ADM_ADM_1']

        for feature in layer:
            name = feature.get('NAME_1')  # Adjust this based on your data structure
            geom = feature.geom.geos

            if isinstance(geom, MultiPolygon):
                health_region, created = HealthRegion.objects.get_or_create(name=name, geom=geom)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created HealthRegion: {name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'HealthRegion already exists: {name}'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'Invalid geometry type for {name}, expected MultiPolygon but got {type(geom)}'))

        # Import Cities (ADM_ADM_2)
        layer = ds['ADM_ADM_2']

        for feature in layer:
            name = feature.get('NAME_2')  # Adjust this based on your data structure
            region_name = feature.get('NAME_1')  # Assuming the city has a reference to the health region
            geom = feature.geom.geos

            if isinstance(geom, MultiPolygon):
                region = HealthRegion.objects.filter(name=region_name).first()
                if region:
                    city, created = City.objects.get_or_create(name=name, region=region, geom=geom)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created City: {name} in {region_name}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'City already exists: {name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'HealthRegion not found for City: {name}'))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Invalid geometry type for City: {name}, expected MultiPolygon but got {type(geom)}'))

# import os
# from django.core.management.base import BaseCommand
# from django.contrib.gis.gdal import DataSource
# from django.contrib.gis.geos import MultiPolygon, Point
# from epidemie.models import HealthRegion, City
#
#
# class Command(BaseCommand):
#     help = 'Import GeoPackage data into Django models'
#
#     def handle(self, *args, **options):
#         gpkg_path = '/Users/ogahserge/Documents/epidemietrackr/static/gadm41_CIV.gpkg'
#
#         if not os.path.exists(gpkg_path):
#             self.stdout.write(self.style.ERROR('GeoPackage file does not exist at the specified path'))
#             return
#
#         ds = DataSource(gpkg_path)
#         layer = ds[0]  # Assuming the first layer contains the HealthRegion data
#
#         for feature in layer:
#             name = feature.get('NAME_1')  # Adjust this based on your data structure
#             geom = feature.geom.geos
#
#             if isinstance(geom, MultiPolygon):
#                 health_region, created = HealthRegion.objects.get_or_create(name=name, geom=geom)
#                 if created:
#                     self.stdout.write(self.style.SUCCESS(f'Created HealthRegion: {name}'))
#                 else:
#                     self.stdout.write(self.style.WARNING(f'HealthRegion already exists: {name}'))
#             else:
#                 self.stdout.write(self.style.ERROR(f'Invalid geometry type for {name}'))
#
#         layer = ds[1]  # Assuming the second layer contains the City data
#
#         for feature in layer:
#             name = feature.get('NAME_2')  # Adjust this based on your data structure
#             region_name = feature.get('NAME_1')  # Assuming the city has a reference to the health region
#             point = feature.geom.geos
#
#             if isinstance(point, Point):
#                 region = HealthRegion.objects.filter(name=region_name).first()
#                 if region:
#                     city, created = City.objects.get_or_create(name=name, region=region, location=point)
#                     if created:
#                         self.stdout.write(self.style.SUCCESS(f'Created City: {name} in {region_name}'))
#                     else:
#                         self.stdout.write(self.style.WARNING(f'City already exists: {name}'))
#                 else:
#                     self.stdout.write(self.style.ERROR(f'HealthRegion not found for City: {name}'))
#             else:
#                 self.stdout.write(self.style.ERROR(f'Invalid geometry type for City: {name}'))
