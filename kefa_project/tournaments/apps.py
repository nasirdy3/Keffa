from django.apps import AppConfig


class TournamentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kefa_project.tournaments'
    
    def ready(self):
        import kefa_project.tournaments.signals
