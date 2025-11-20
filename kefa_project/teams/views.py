from django.shortcuts import render, get_object_or_404
from .models import Team
from kefa_project.tournaments.models import Standing
from kefa_project.matches.models import Match
from kefa_project.highlights.models import Highlight


def team_profile(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    player = team.player
    
    standings = Standing.objects.filter(team=team).order_by('-points')
    
    all_matches = Match.objects.filter(
        home_team=team
    ) | Match.objects.filter(
        away_team=team
    )
    all_matches = all_matches.order_by('-match_date', '-match_time')
    
    highlights = Highlight.objects.filter(
        uploaded_by_team=team,
        status='verified'
    ).order_by('-verified_at')[:10]
    
    badges = player.badges.all().select_related('badge', 'tournament')
    trophies = team.trophies.all().select_related('tournament')
    
    stats = {
        'total_matches': all_matches.filter(status='completed').count(),
        'total_wins': 0,
        'total_draws': 0,
        'total_losses': 0,
        'total_goals_scored': sum(s.goals_for for s in standings),
        'total_goals_conceded': sum(s.goals_against for s in standings),
    }
    
    for standing in standings:
        stats['total_wins'] += standing.won
        stats['total_draws'] += standing.drawn
        stats['total_losses'] += standing.lost
    
    return render(request, 'teams/profile.html', {
        'team': team,
        'player': player,
        'standings': standings[:5],
        'recent_matches': all_matches[:10],
        'highlights': highlights,
        'badges': badges,
        'trophies': trophies,
        'stats': stats
    })
