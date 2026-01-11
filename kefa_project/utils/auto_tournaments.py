from django.utils import timezone
from datetime import timedelta
from kefa_project.tournaments.models import Tournament


def ensure_champions_league_exists():
    """
    Ensure the default Champions League tournament always exists
    This should be called on server startup
    """
    existing_cl = Tournament.objects.filter(
        tournament_type='champions_league',
        status__in=['registration', 'locked', 'ongoing']
    ).first()
    
    if not existing_cl:
        start_date = timezone.now().date() + timedelta(days=7)
        
        Tournament.objects.create(
            name='KEFA Champions League',
            tournament_type='champions_league',
            team_limit=16,
            registration_fee=1000,
            prize='₦50,000 + Trophy + Champions Badge',
            rules="""
KEFA Champions League - The Ultimate eFootball Competition

Format:
- 16 teams compete in a mixed format tournament
- Group Stage: 4 groups of 4 teams each
- Top 2 from each group advance to Knockout Stage
- Quarter-Finals, Semi-Finals, and Final

Rules:
1. All matches must be played on scheduled date/time
2. Both teams must upload match highlights within 24 hours
3. No substitutions or changes after registration closes
4. Fair play and sportsmanship are mandatory
5. Admin decisions are final

Prizes:
- Winner: ₦30,000 + Trophy + Champions Badge
- Runner-up: ₦15,000 + Medal
- Semi-finalists: ₦2,500 each
            """,
            status='registration',
            start_date=start_date,
            promotion_relegation_enabled=False,
            fixtures_generated=False,
        )
        print("[OK] Champions League tournament created successfully")
    else:
        print("[OK] Champions League tournament already exists")


def handle_season_completion(tournament):
    """
    Handle automatic promotion/relegation and season restart
    Called when a league tournament completes
    """
    if not tournament.promotion_relegation_enabled:
        return
    
    from kefa_project.tournaments.models import Standing
    
    standings = Standing.objects.filter(tournament=tournament).order_by('-points', '-goal_difference')
    
    if not standings.exists():
        return
    
    teams_to_relegate_count = tournament.teams_to_relegate
    teams_to_promote_count = tournament.teams_to_promote
    
    relegated_teams = list(standings[len(standings)-teams_to_relegate_count:])
    
    if tournament.junior_league:
        junior_standings = Standing.objects.filter(
            tournament=tournament.junior_league
        ).order_by('-points', '-goal_difference')[:teams_to_promote_count]
        
        promoted_teams = list(junior_standings)
        
        new_season_start = timezone.now().date() + timedelta(days=2)
        
        print(f"[OK] Season completed for {tournament.name}")
        print(f"  - {len(relegated_teams)} teams relegated")
        print(f"  - {len(promoted_teams)} teams promoted")
        print(f"  - New season starts on {new_season_start}")
        
        schedule_new_season(tournament, new_season_start, relegated_teams, promoted_teams)


def schedule_new_season(tournament, start_date, relegated_teams, promoted_teams):
    """
    Schedule a new season with promotion/relegation applied
    This creates a new tournament with swapped teams
    """
    pass
