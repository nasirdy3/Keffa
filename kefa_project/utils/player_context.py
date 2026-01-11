from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

def get_performance_context(request):
    """
    Safely retrieves player and team context for the current user.
    Returns a tuple: (player, team, error_response)
    
    If error_response is not None, the caller should return it immediately.
    """
    user = request.user
    if not user.is_authenticated:
        # Should be covered by @login_required but safe to keep
        return None, None, redirect('login')

    try:
        player = user.player_profile
    except ObjectDoesNotExist:
        if user.is_staff or user.is_superuser:
            # Admins might not have player profiles, but shouldn't crash
            # We return None for player but allow flow to continue if logic permits,
            # OR we redirect them if the view strictly needs a player.
            # For now, we mimic old behavior: redirect to admin dashboard or show error
            messages.warning(request, "Admin account detected without Player Profile. Some features may be limited.")
            return None, None, None # Caller must handle None player for admins
        
        messages.error(request, 'Player profile not found. Please contact support.')
        return None, None, redirect('home')

    try:
        team = player.team
    except ObjectDoesNotExist:
        team = None

    return player, team, None

def require_team(request, func_name="Access"):
    """
    Strictly requires a team. Returns (player, team, response).
    usage:
        player, team, resp = require_team(request)
        if resp: return resp
    """
    player, team, resp = get_performance_context(request)
    if resp:
        return None, None, resp
    
    if not player and (request.user.is_staff or request.user.is_superuser):
         # Admin Bypass - CAUTION: Views must handle team=None if they allow admins
         return None, None, None

    if not team:
        messages.error(request, f'You must have a team to {func_name}.')
        return None, None, redirect('players:player_dashboard')
        
    return player, team, None
