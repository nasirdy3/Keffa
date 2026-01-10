from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from kefa_project.matches.models import Match
from kefa_project.teams.models import Team
from .models import Badge, PlayerBadge

def calculate_player_of_the_week():
    """
    Identifies the Captain of the best performing team of the last 7 days.
    Criteria: Most Wins -> Most Goals Scored -> Least Goals Conceded.
    Awards the 'Player of the Week' badge.
    """
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    
    # Get completed matches in last 7 days
    recent_matches = Match.objects.filter(
        status='completed',
        match_date__gte=seven_days_ago.date(),
        match_date__lte=now.date()
    )
    
    if not recent_matches.exists():
        return None
        
    # We need to manually aggregate because Match data is normalized
    team_stats = {}
    
    for match in recent_matches:
        # Home Team Stats
        h_id = match.home_team.id
        if h_id not in team_stats: team_stats[h_id] = {'wins': 0, 'goals': 0, 'conceded': 0}
        
        team_stats[h_id]['goals'] += match.home_score if match.home_score else 0
        team_stats[h_id]['conceded'] += match.away_score if match.away_score else 0
        if match.home_score > match.away_score:
            team_stats[h_id]['wins'] += 1
            
        # Away Team Stats
        a_id = match.away_team.id
        if a_id not in team_stats: team_stats[a_id] = {'wins': 0, 'goals': 0, 'conceded': 0}
        
        team_stats[a_id]['goals'] += match.away_score if match.away_score else 0
        team_stats[a_id]['conceded'] += match.home_score if match.home_score else 0
        if match.away_score > match.home_score:
            team_stats[a_id]['wins'] += 1
            
    if not team_stats:
        return None
        
    # Sort teams: Wins desc, Goals desc, Conceded asc
    sorted_teams = sorted(
        team_stats.items(), 
        key=lambda item: (-item[1]['wins'], -item[1]['goals'], item[1]['conceded'])
    )
    
    best_team_id = sorted_teams[0][0]
    best_team = Team.objects.get(id=best_team_id)
    player = best_team.player # Access the PlayerProfile
    
    # Award Badge
    badge, _ = Badge.objects.get_or_create(
        name='Player of the Week',
        defaults={
            'badge_type': 'player_of_week',
            'description': f"Captain of the best performing team ({best_team.team_name}) for the week.",
            'is_automatic': True
        }
    )
    
    # Check if already awarded this week to avoid duplicates
    if not PlayerBadge.objects.filter(player=player, badge=badge, awarded_at__gte=seven_days_ago).exists():
        PlayerBadge.objects.create(
            player=player,
            badge=badge,
            notes=f"Led {best_team.team_name} to {team_stats[best_team_id]['wins']} wins and {team_stats[best_team_id]['goals']} goals."
        )
        return player
        
    return None

def check_match_milestones(team):
    """
    Checks and awards milestone badges (First Win, 10 Matches, etc.)
    Should be called after a match is completed.
    """
    player = team.player
    
    # 1. Total Matches Milestones
    total_matches = Match.objects.filter(
        (Q(home_team=team) | Q(away_team=team)),
        status='completed'
    ).count()
    
    if total_matches == 1:
        _award_milestone(player, 'first_match', 'First Match Played', 'Awarded for completing your first match.')
    elif total_matches == 10:
        _award_milestone(player, '10_matches', 'Veteran (10 Matches)', 'Awarded for completing 10 matches.')
    elif total_matches == 50:
        _award_milestone(player, '50_matches', 'Club Legend (50 Matches)', 'Awarded for completing 50 matches.')

    # 2. Total Wins Milestones
    # We can query Standings or aggregate Matches. Standings is per tournament, so aggregate matches for career stats.
    home_wins = Match.objects.filter(home_team=team, status='completed', home_score__gt=models.F('away_score')).count()
    away_wins = Match.objects.filter(away_team=team, status='completed', away_score__gt=models.F('home_score')).count()
    total_wins = home_wins + away_wins
    
    if total_wins == 1:
        _award_milestone(player, 'first_win', 'First Victory', 'Awarded for winning your first match.')
    elif total_wins == 10:
        _award_milestone(player, '10_wins', 'Winner (10 Wins)', 'Awarded for winning 10 matches.')

def _award_milestone(player, unique_id, name, description):
    badge, _ = Badge.objects.get_or_create(
        name=name,
        defaults={
            'badge_type': 'custom', # Storing milestones as custom or we can add new types to choices
            'description': description,
            'is_automatic': True
        }
    )
    
    if not PlayerBadge.objects.filter(player=player, badge=badge).exists():
        PlayerBadge.objects.create(player=player, badge=badge, notes="Milestone Achievement")


def award_automatic_achievements(tournament):
    """
    Checks for any tournament-wide achievements that should be awarded.
    Triggered after match verification.
    """
    # Placeholder for logic that checks for specific tournament-wide badges
    # unrelated to specific match milestones (which are handled in check_match_milestones)
    pass
