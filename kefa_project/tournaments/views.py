from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from .models import Tournament, Standing, TournamentRegistration
from kefa_project.matches.models import Match


def tournaments_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at')
    
    active_tournaments = tournaments.filter(status__in=['registration', 'locked', 'ongoing'])
    completed_tournaments = tournaments.filter(status='completed')
    
    return render(request, 'tournaments/list.html', {
        'active_tournaments': active_tournaments,
        'completed_tournaments': completed_tournaments
    })


def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Optimized: select_related to prevent N+1 queries on team names
    standings = Standing.objects.filter(tournament=tournament).select_related('team').order_by(
        '-points', 
        (F('goals_for') - F('goals_against')).desc(), 
        '-goals_for'
    )
    
    # Optimized: fetch specific matches with team data
    fixtures = Match.objects.filter(tournament=tournament).select_related('home_team', 'away_team').order_by('match_date', 'match_time')
    
    upcoming_fixtures = fixtures.filter(status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress', 'postponed', 'awaiting_highlight', 'pending_verification'])
    completed_fixtures = fixtures.filter(status__in=['completed', 'home_forfeit', 'away_forfeit', 'both_forfeit']).order_by('-match_date', '-match_time', '-id')
    
    user_team = None
    user_registered = False
    if request.user.is_authenticated:
        try:
            player = request.user.player_profile
            user_team = player.team
            user_registered = TournamentRegistration.objects.filter(
                tournament=tournament,
                team=user_team,
                payment_verified=True
            ).exists()
        except:
            pass
    
    # Get today's date for template
    from datetime import date
    today = date.today()
    
    return render(request, 'tournaments/detail.html', {
        'tournament': tournament,
        'standings': standings,
        'upcoming_fixtures': upcoming_fixtures,
        'completed_fixtures': completed_fixtures,
        'user_team': user_team,
        'user_registered': user_registered,
        'total_matches': fixtures.count(),
        'today': today,
    })



def tournament_standings(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    standings = Standing.objects.filter(tournament=tournament).select_related('team').order_by(
        '-points', 
        (F('goals_for') - F('goals_against')).desc(), 
        '-goals_for'
    )
    
    return render(request, 'tournaments/standings.html', {
        'tournament': tournament,
        'standings': standings
    })


def tournament_fixtures(request, tournament_id):
    """
    Displays the full calendar of matches for the tournament.
    """
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Fetch ALL matches ordered by date/time for the timeline view
    # select_related is crucial here for performance
    fixtures = Match.objects.filter(tournament=tournament).select_related('home_team', 'away_team').order_by('match_date', 'match_time')
    
    return render(request, 'tournaments/fixtures.html', {
        'tournament': tournament,
        'fixtures': fixtures, 
    })


def tournament_top_scorers(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    standings = Standing.objects.filter(tournament=tournament).select_related('team').order_by('-goals_for')[:20]
    

@login_required
def finalize_tournament(request, tournament_id):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access Denied")
        return redirect('tournaments:detail', tournament_id=tournament_id)
        
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        from .services import process_season_end
        success, message = process_season_end(tournament)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
            
    return redirect('tournaments:detail', tournament_id=tournament_id)

