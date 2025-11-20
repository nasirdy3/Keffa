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
    
    total_matches = all_matches.filter(status='completed').count()
    total_wins = sum(s.won for s in standings)
    total_draws = sum(s.drawn for s in standings)
    total_losses = sum(s.lost for s in standings)
    
    win_rate = round((total_wins / total_matches * 100) if total_matches > 0 else 0, 1)
    trophies_count = trophies.count()
    
    return render(request, 'teams/profile.html', {
        'team': team,
        'player': player,
        'standings': standings[:5],
        'recent_matches': all_matches[:10],
        'highlights': highlights,
        'badges': badges,
        'trophies': trophies,
        'total_matches': total_matches,
        'total_wins': total_wins,
        'win_rate': win_rate,
        'trophies_count': trophies_count,
    })
