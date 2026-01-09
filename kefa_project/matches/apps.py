from django.apps import AppConfig

class MatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kefa_project.matches'

    def ready(self):
        import kefa_project.matches.signals

