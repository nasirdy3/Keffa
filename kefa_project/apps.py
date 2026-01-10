from django.apps import AppConfig


class KefaProjectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kefa_project'
    
    def ready(self):
        """
        Initialize KEFA platform on startup
        """
        pass
