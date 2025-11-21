from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import TournamentRegistration, Tournament
from .services import lock_and_generate_fixtures, regenerate_fixtures


@receiver(post_save, sender=TournamentRegistration)
def check_tournament_full(sender, instance, created, **kwargs):
    if not (created or instance.payment_verified):
        return
    
    tournament = instance.tournament
    
    if tournament.status == 'registration' and tournament.is_full and not tournament.fixtures_generated:
        with transaction.atomic():
            tournament.status = 'locked'
            tournament.fixtures_generated = True
            tournament.save()
            
            lock_and_generate_fixtures(tournament)
    
    elif tournament.fixtures_generated and instance.payment_verified:
        if tournament.tournament_type in ['league', 'champions_league']:
            with transaction.atomic():
                regenerate_fixtures(tournament)
