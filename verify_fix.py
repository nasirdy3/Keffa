from django.db.models import Q
from kefa_project.matches.models import Match
from kefa_project.teams.models import Team
from kefa_project.tournaments.models import Tournament
from datetime import date, time

# Clear any existing repro matches
Match.objects.filter(tournament__name='Repro Tournament').delete()
Tournament.objects.filter(name='Repro Tournament').delete()

# Setup repro data
t = Tournament.objects.create(name='Repro Tournament', start_date=date.today(), end_date=date.today(), status='active')
team = Team.objects.first()
opponent = Team.objects.last()

if team and opponent:
    # Create matches with different dates/times and statuses
    Match.objects.create(tournament=t, home_team=team, away_team=opponent, match_date=date(2025,1,12), match_time=time(10,0), status='scheduled')
    Match.objects.create(tournament=t, home_team=team, away_team=opponent, match_date=date(2025,1,10), match_time=time(14,0), status='postponed')
    Match.objects.create(tournament=t, home_team=team, away_team=opponent, match_date=date(2025,1,10), match_time=time(0,0), status='ready_pending')
    Match.objects.create(tournament=t, home_team=team, away_team=opponent, match_date=date(2025,1,11), match_time=time(10,0), status='pending_verification')

    # Query from player dashboard
    upcoming_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress', 'awaiting_highlight', 'postponed', 'pending_verification']
    ).distinct().order_by('match_date', 'match_time', 'id')

    print("\n--- Match Dashboard Verification ---")
    for m in upcoming_matches:
        print(f"Date: {m.match_date}, Time: {m.match_time}, Status: {m.status}")

    # Query from tournament detail (upcoming)
    upcoming_fixtures = Match.objects.filter(tournament=t).filter(
        status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress', 'postponed', 'awaiting_highlight', 'pending_verification']
    ).order_by('match_date', 'match_time', 'id')

    print("\n--- Tournament Fixture Verification ---")
    for m in upcoming_fixtures:
        print(f"Date: {m.match_date}, Time: {m.match_time}, Status: {m.status}")
else:
    print("Insufficient teams for repro.")
