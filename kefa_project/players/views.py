from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from .forms import UserRegistrationForm, PlayerProfileForm
from kefa_project.teams.forms import TeamForm
from .models import Player, GovernanceLog
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator

User = get_user_model()

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
                    return redirect('players:player_dashboard')
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
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            # Direct admins/staff to governance dashboard
            if user.is_staff or user.is_superuser:
                return redirect('players:governance_dashboard')
                
            return redirect('players:player_dashboard')
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
    from kefa_project.tournaments.models import TournamentRegistration
    from kefa_project.achievements.models import PlayerBadge

    try:
        player = request.user.player_profile
        team = player.team
    except Player.DoesNotExist:
        # ARCHITECT FIX: Handle Superusers/Admins who don't have a Player profile
        if request.user.is_superuser or request.user.is_staff:
            # This redirect now maps correctly to 'players:governance_dashboard' in urls.py
            return redirect('players:governance_dashboard')
            
        messages.error(request, 'Player profile not found. Please contact support.')
        return redirect('home')
    except Exception:
        # Fallback for other relationship errors (e.g., Player exists but Team missing)
        messages.error(request, 'Team data missing. Please update your profile.')
        return redirect('players:edit_profile')

    # Get tournament registrations
    tournaments_count = TournamentRegistration.objects.filter(
        team=team,
        payment_verified=True
    ).count()

    # Get matches statistics
    completed_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status='completed'
    ).distinct()
    
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

    # Get upcoming/active matches
    upcoming_matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status__in=['scheduled', 'ready_pending', 'creating_game', 'waiting_join', 'in_progress', 'awaiting_highlight', 'postponed', 'pending_verification']
    ).distinct().order_by('match_date', 'match_time', 'id')

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

@login_required
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
            Q(home_team=team) | Q(away_team=team)
        ).distinct()
        
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
            return redirect('players:player_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        player_form = PlayerProfileForm(instance=player)
        team_form = TeamForm(instance=team)

    return render(request, 'players/edit_profile.html', {
        'player_form': player_form,
        'team_form': team_form,
    })

# --- ARCHITECT NOTE: Governance Logic Implementation ---

@login_required
def governance_dashboard(request):
    """
    Central Governance Hub.
    - Admins: See everything + Role Management + Audit Logs.
    - Moderators: See verification queues (Payments, Matches, Highlights).
    - Users: Redirected to player dashboard.
    """
    
    # ARCHITECT FIX: Safely determine Role and Profile existence
    try:
        profile = request.user.player_profile
        role = profile.role
    except (Player.DoesNotExist, AttributeError):
        # If user is Superuser/Staff but has no profile, treat as Admin
        if request.user.is_superuser or request.user.is_staff:
            profile = None # Explicitly None for template handling
            role = 'admin'
        else:
            messages.error(request, "Profile access error. Specialized profile required.")
            return redirect('home')

    # Access Control: Only Admins and Moderators allowed
    is_admin = (role == 'admin') or request.user.is_superuser
    is_moderator = (role == 'moderator')
    
    if not (is_admin or is_moderator):
        messages.warning(request, "Access restricted to KEFA officials.")
        return redirect('players:player_dashboard')

    # Imports for data aggregation
    from kefa_project.payments.models import Payment
    from kefa_project.matches.models import Match
    from kefa_project.highlights.models import Highlight
    from kefa_project.tournaments.models import Tournament

    # --- ACTION: Handle Role Changes (Admin Only) ---
    if request.method == 'POST' and 'update_role' in request.POST and is_admin:
        target_username = request.POST.get('target_username')
        new_role = request.POST.get('new_role')
        
        try:
            target_user = User.objects.get(username=target_username)
            # Check if target has profile
            if hasattr(target_user, 'player_profile'):
                target_profile = target_user.player_profile
                old_role = target_profile.role
                
                if old_role != new_role:
                    target_profile.role = new_role
                    target_profile.save()
                    
                    # Update Django permissions for compatibility
                    if new_role in ['admin', 'moderator']:
                        target_user.is_staff = True
                    else:
                        target_user.is_staff = False
                    target_user.save()
                    
                    # Log the action
                    GovernanceLog.objects.create(
                        admin=request.user,
                        action='role_change',
                        target_object=f"User: {target_username}",
                        details=f"Changed role from {old_role} to {new_role}"
                    )
                    messages.success(request, f"Role for {target_username} updated to {new_role}.")
            else:
                messages.error(request, f"User {target_username} has no Player Profile to update.")

        except User.DoesNotExist:
            messages.error(request, "User not found.")
        except Exception as e:
            messages.error(request, f"Error updating role: {str(e)}")
        
        # ARCHITECT FIX: Correct redirect to self (namespaced)
        return redirect('players:governance_dashboard')

    # --- DATA GATHERING ---
    
    # 1. Verification Queues (For Mods & Admins)
    pending_payments = Payment.objects.filter(status='pending').count()
    pending_highlights = Highlight.objects.filter(status='pending').count()
    disputed_matches = Match.objects.filter(status='pending_verification').count()
    
    # 2. Statistics
    total_players = Player.objects.count()
    active_tournaments = Tournament.objects.filter(status__in=['registration_open', 'active']).count()
    total_revenue = Payment.objects.filter(status='verified').aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'profile': profile,
        'is_admin': is_admin,
        'pending_payments': pending_payments,
        'pending_highlights': pending_highlights,
        'disputed_matches': disputed_matches,
        'total_players': total_players,
        'active_tournaments': active_tournaments,
        'total_revenue': total_revenue,
    }

    # 3. Admin Specific Data (Role Management & Logs)
    if is_admin:
        # Fetch recent logs
        audit_logs = GovernanceLog.objects.all()[:20]
        context['audit_logs'] = audit_logs
        
        # Simple user search for role management
        users_list = User.objects.select_related('player_profile').all().order_by('-date_joined')[:50]
        context['users_list'] = users_list

    return render(request, 'admin/governance_dashboard.html', context)

