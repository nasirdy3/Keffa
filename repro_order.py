import os
import django
from datetime import date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kefa_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.tournaments.models import Tournament
from kefa_project.matches.models import Match
from django.db.models import Q

def run():
    # Create dummy data if not exists
    User = get_user_model()
    user, _ = User.objects.get_or_create(username='repro_user')
    player, _ = Player.objects.get_or_create(user=user, full_name='Repro Player')
    team, _ = Team.objects.get_or_create(player=player, team_name='Repro Team')
    
    t, _ = Tournament.objects.get_or_create(name='Repro Tournament', start_date=date.today(), end_date=date.today())

    # Create matches with different dates
    dates = [
        (date(2025, 1, 10), time(10, 0)),
        (date(2025, 1, 12), time(10, 0)),
        (date(2025, 1, 11), time(10, 0)),
    ]
    
    opponent, _ = Team.objects.get_or_create(team_name='Opponent')

    for d, ti in dates:
        Match.objects.get_or_create(
            tournament=t,
            home_team=team,
            away_team=opponent,
            match_date=d,
            match_time=ti,
            status='scheduled'
        )

    # Run the query from the view
    upcoming_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress', 'awaiting_highlight']
    ).distinct().order_by('match_date', 'match_time')
    
    print("Query SQL:", upcoming_matches.query)
    
    print("\nResults:")
    for m in upcoming_matches:
        print(f"{m.match_date} {m.match_time} - {m.pk}")

if __name__ == '__main__':
    run()
