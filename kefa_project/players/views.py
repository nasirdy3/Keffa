from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import UserRegistrationForm, PlayerProfileForm
from kefa_project.teams.forms import TeamForm
from .models import Player

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        player_form = PlayerProfileForm(request.POST, request.FILES)
        team_form = TeamForm(request.POST, request.FILES)
        
        if user_form.is_valid() and player_form.is_valid() and team_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save()
                    
                    player = player_form.save(commit=False)
                    player.user = user
                    player.save()
                    
                    team = team_form.save(commit=False)
                    team.player = player
                    team.save()
                    
                    login(request, user)
                    messages.success(request, f'Welcome to KEFA, {player.full_name}! Your account has been created successfully.')
                    return redirect('player_dashboard')
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegistrationForm()
        player_form = PlayerProfileForm()
        team_form = TeamForm()
    
    return render(request, 'players/register.html', {
        'user_form': user_form,
        'player_form': player_form,
        'team_form': team_form,
    })


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'player_dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'players/login.html')


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def player_dashboard(request):
    from kefa_project.matches.models import Match
    from kefa_project.tournaments.models import TournamentRegistration, Standing
    from kefa_project.achievements.models import PlayerBadge
    from django.db.models import Q, Count
    
    try:
        player = request.user.player_profile
        team = player.team
    except Player.DoesNotExist:
        messages.error(request, 'Player profile not found. Please contact support.')
        return redirect('home')
    
    # Get tournament registrations
    tournaments_count = TournamentRegistration.objects.filter(
        team=team,
        payment_verified=True
    ).count()
    
    # Get matches statistics
    completed_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status='completed'
    )
    matches_count = completed_matches.count()
    
    # Calculate win rate
    wins = 0
    for match in completed_matches:
        if match.home_team == team and match.home_score > match.away_score:
            wins += 1
        elif match.away_team == team and match.away_score > match.home_score:
            wins += 1
    
    win_rate = round((wins / matches_count * 100) if matches_count > 0 else 0, 1)
    
    # Get achievements count
    achievements_count = PlayerBadge.objects.filter(player=player).count()
    
    # Get upcoming matches
    upcoming_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress', 'awaiting_highlight']
    ).order_by('match_date', 'match_time')[:5]
    
    # Get recent achievements
    recent_achievements = PlayerBadge.objects.filter(
        player=player
    ).select_related('badge').order_by('-awarded_at')[:5]
    
    return render(request, 'players/dashboard.html', {
        'player': player,
        'team': team,
        'tournaments_count': tournaments_count,
        'matches_count': matches_count,
        'win_rate': win_rate,
        'achievements_count': achievements_count,
        'upcoming_matches': upcoming_matches,
        'recent_achievements': recent_achievements,
    })


def player_profile(request, player_id):
    from kefa_project.tournaments.models import Standing
    from kefa_project.matches.models import Match
    from kefa_project.highlights.models import Highlight
    
    player = get_object_or_404(Player, id=player_id)
    try:
        team = player.team
    except:
        team = None
    
    if team:
        standings = Standing.objects.filter(team=team).order_by('-points')[:5]
        all_matches = Match.objects.filter(
            home_team=team
        ) | Match.objects.filter(
            away_team=team
        )
        recent_matches = all_matches.order_by('-match_date', '-match_time')[:10]
        
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
    else:
        standings = []
        recent_matches = []
        highlights = []
        badges = []
        trophies = []
        total_matches = 0
        total_wins = 0
        total_draws = 0
        total_losses = 0
        win_rate = 0
    
    return render(request, 'players/profile.html', {
        'player': player,
        'team': team,
        'standings': standings,
        'recent_matches': recent_matches,
        'highlights': highlights,
        'badges': badges,
        'trophies': trophies,
        'total_matches': total_matches,
        'total_wins': total_wins,
        'total_draws': total_draws,
        'total_losses': total_losses,
        'win_rate': win_rate,
    })


@login_required
def edit_profile(request):
    player = request.user.player_profile
    team = player.team
    
    if request.method == 'POST':
        player_form = PlayerProfileForm(request.POST, request.FILES, instance=player)
        team_form = TeamForm(request.POST, request.FILES, instance=team)
        
        if player_form.is_valid() and team_form.is_valid():
            player_form.save()
            team_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('player_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        player_form = PlayerProfileForm(instance=player)
        team_form = TeamForm(instance=team)
    
    return render(request, 'players/edit_profile.html', {
        'player_form': player_form,
        'team_form': team_form,
    })
