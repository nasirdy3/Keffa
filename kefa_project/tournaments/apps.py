from django.apps import AppConfig


from django.db.models.signals import post_migrate

def create_default_tournaments(sender, **kwargs):
    from kefa_project.utils.auto_tournaments import ensure_champions_league_exists
    try:
        ensure_champions_league_exists()
    except Exception as e:
        print(f"Error initializing Champions League: {e}")

class TournamentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kefa_project.tournaments'
    
    def ready(self):
        import kefa_project.tournaments.signals
        post_migrate.connect(create_default_tournaments, sender=self)
