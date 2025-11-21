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
    
    standings = Standing.objects.filter(tournament=tournament).order_by('-points', (F('goals_for') - F('goals_against')).desc(), '-goals_for')
    fixtures = Match.objects.filter(tournament=tournament).order_by('match_date', 'match_time')
    
    upcoming_fixtures = fixtures.filter(status__in=['scheduled', 'ready_pending'])
    completed_fixtures = fixtures.filter(status='completed')
    
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
    
    return render(request, 'tournaments/detail.html', {
        'tournament': tournament,
        'standings': standings,
        'upcoming_fixtures': upcoming_fixtures[:10],
        'completed_fixtures': completed_fixtures[:10],
        'user_team': user_team,
        'user_registered': user_registered
    })


def tournament_standings(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    standings = Standing.objects.filter(tournament=tournament).order_by('-points', (F('goals_for') - F('goals_against')).desc(), '-goals_for')
    
    return render(request, 'tournaments/standings.html', {
        'tournament': tournament,
        'standings': standings
    })


def tournament_fixtures(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    fixtures = Match.objects.filter(tournament=tournament).order_by('match_date', 'match_time')
    
    upcoming = fixtures.filter(status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress'])
    completed = fixtures.filter(status__in=['completed', 'home_forfeit', 'away_forfeit', 'both_forfeit'])
    
    return render(request, 'tournaments/fixtures.html', {
        'tournament': tournament,
        'upcoming_fixtures': upcoming,
        'completed_fixtures': completed
    })


def tournament_top_scorers(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    standings = Standing.objects.filter(tournament=tournament).order_by('-goals_for')[:20]
    
    return render(request, 'tournaments/top_scorers.html', {
        'tournament': tournament,
        'top_scorers': standings
    })
