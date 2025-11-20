from django.shortcuts import render
from django.db.models import Count
from kefa_project.tournaments.models import Tournament
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.matches.models import Match


def home(request):
    """Homepage view with platform statistics"""
    
    # Get statistics
    total_players = Player.objects.count()
    total_teams = Team.objects.count()
    active_tournaments = Tournament.objects.filter(
        status__in=['registration', 'locked', 'ongoing']
    ).count()
    total_matches = Match.objects.filter(status='completed').count()
    
    # Get featured tournaments (active ones)
    featured_tournaments = Tournament.objects.filter(
        status__in=['registration', 'ongoing']
    ).order_by('-created_at')[:3]
    
    context = {
        'total_players': total_players,
        'total_teams': total_teams,
        'active_tournaments': active_tournaments,
        'total_matches': total_matches,
        'featured_tournaments': featured_tournaments,
    }
    
    return render(request, 'home.html', context)
