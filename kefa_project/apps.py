from django.apps import AppConfig


class KefaProjectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kefa_project'
    
    def ready(self):
        """
        Initialize KEFA platform on startup
        """
        import os
        
        if os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            return
        
        try:
            from kefa_project.utils.auto_tournaments import ensure_champions_league_exists
            ensure_champions_league_exists()
        except Exception as e:
            print(f"Error initializing Champions League: {e}")
