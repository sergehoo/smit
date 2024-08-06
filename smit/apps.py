from django.apps import AppConfig


class SmitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smit'

    def ready(self):
        import smit.signals
