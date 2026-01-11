from django.shortcuts import render
from django.db import models
from django.db.models import Count, Sum, Q
from kefa_project.tournaments.models import Tournament, Standing
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.matches.models import Match
from kefa_project.highlights.models import Highlight
from kefa_project.payments.models import Payment
from datetime import date


def home(request):
    # Get active tournaments (registration open or ongoing)
    featured_tournaments = Tournament.objects.filter(
        status__in=['registration', 'locked', 'ongoing']
    ).annotate(
        teams_count=Count('registrations', filter=models.Q(registrations__payment_verified=True))
    ).order_by('-created_at')[:6]
    
    # Get live matches (in progress)
    live_matches = Match.objects.filter(
        status='in_progress'
    ).select_related('tournament', 'home_team', 'away_team').order_by('match_date', 'match_time')[:10]
    
    # Get upcoming matches today
    today = date.today()
    upcoming_today = Match.objects.filter(
        match_date=today,
        status='scheduled'
    ).select_related('tournament', 'home_team', 'away_team').order_by('match_time')[:10]
    
    # Player of the Week
    from kefa_project.achievements.services import calculate_player_of_the_week
    player_of_week = calculate_player_of_the_week()
    
    context = {
        'featured_tournaments': featured_tournaments,
        'live_matches': live_matches,
        'upcoming_today': upcoming_today,
        'player_of_week': player_of_week,
    }
    
    return render(request, 'home.html', context)





def leaderboards(request):
    """Leaderboards showing top teams and top scorers"""
    
    top_teams = Standing.objects.select_related('team', 'tournament').order_by('-points', '-goals_for')[:20]
    
    top_scorers = Standing.objects.select_related('team__player', 'tournament').filter(
        goals_for__gt=0
    ).order_by('-goals_for')[:20]
    
    top_players = Player.objects.annotate(
        achievements_count=Count('badges')
    ).filter(achievements_count__gt=0).order_by('-achievements_count')[:20]
    
    context = {
        'top_teams': top_teams,
        'top_scorers': top_scorers,
        'top_players': top_players,
    }
    
    return render(request, 'leaderboards.html', context)
    return render(request, 'leaderboards.html', context)


from django.contrib.auth.decorators import login_required
from kefa_project.players.views import governance_dashboard

@login_required
def governance_dashboard_alias(request):
    """
    Alias view to allow access via /admin-dashboard/ and /moderator-dashboard/
    Redirects logic to the actual governance dashboard implementation.
    """
    return governance_dashboard(request)
