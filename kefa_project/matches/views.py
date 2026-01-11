from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from .models import Match, MatchPostponement, FriendlyMatch
from kefa_project.teams.models import Team


from kefa_project.utils.player_context import require_team

@login_required
def match_ready(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    player, team, error_resp = require_team(request, func_name="mark ready")
    if error_resp:
        return error_resp
    
    if match.status != 'ready_pending':
        messages.error(request, 'This match is not in ready phase.')
        return redirect('players:player_dashboard')
    
    if match.home_team == team:
        match.home_ready = True
        match.save()
        messages.success(request, 'You are marked as ready!')
    elif match.away_team == team:
        match.away_ready = True
        match.save()
        messages.success(request, 'You are marked as ready!')
    else:
        messages.error(request, 'This is not your match.')
        return redirect('players:player_dashboard')
    
    # ARCHITECT NOTE: If both teams are ready, move directly to in_progress.
    # Players are expected to coordinate via WhatsApp now.
    if match.home_ready and match.away_ready:
        match.status = 'in_progress'
        match.save()
        messages.success(request, 'Both teams ready! Connect on WhatsApp to play.')
    
    return redirect('players:player_dashboard')


@login_required
def match_finished(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    player, team, error_resp = require_team(request, func_name="finish match")
    if error_resp:
        return error_resp
    
    if match.home_team != team and match.away_team != team:
        messages.error(request, 'This is not your match.')
        return redirect('players:player_dashboard')
    
    if match.status == 'in_progress':
        match.status = 'awaiting_highlight'
        match.save()
        messages.success(request, 'Match marked as finished. Please upload your highlight.')
    
    return redirect('players:player_dashboard')


@login_required
def request_postponement(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    player, team, error_resp = require_team(request, func_name="request postponement")
    if error_resp:
        return error_resp
    
    if match.home_team != team and match.away_team != team:
        messages.error(request, 'This is not your match.')
        return redirect('players:player_dashboard')
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        proposed_date = request.POST.get('proposed_date')
        proposed_time = request.POST.get('proposed_time')
        
        if reason and proposed_date and proposed_time:
            postponement = MatchPostponement.objects.create(
                match=match,
                requested_by=team,
                reason=reason,
                proposed_date=proposed_date,
                proposed_time=proposed_time,
                status='requested'
            )
            messages.success(request, 'Postponement request submitted. Waiting for opponent acceptance.')
            return redirect('players:player_dashboard')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'matches/request_postponement.html', {'match': match})


@login_required
def accept_postponement(request, postponement_id):
    postponement = get_object_or_404(MatchPostponement, id=postponement_id)
    match = postponement.match
    
    player, team, error_resp = require_team(request, func_name="accept postponement")
    if error_resp:
        return error_resp
    
    opponent_team = match.away_team if match.home_team == postponement.requested_by else match.home_team
    
    if team != opponent_team:
        messages.error(request, 'You cannot accept this postponement request.')
        return redirect('players:player_dashboard')
    
    if postponement.status == 'requested':
        postponement.opponent_accepted = True
        postponement.status = 'pending_admin'
        postponement.save()
        messages.success(request, 'Postponement accepted. Request sent to admin for approval.')
    
    return redirect('players:player_dashboard')


@login_required
def create_friendly_match(request):
    player, team, error_resp = require_team(request, func_name="create friendly match")
    if error_resp:
        return error_resp
    
    if request.method == 'POST':
        game_code = request.POST.get('game_code', '').strip()
        
        if game_code:
            friendly = FriendlyMatch.objects.create(
                created_by_team=team,
                game_code=game_code,
                status='open'
            )
            messages.success(request, f'Friendly match created with code: {game_code}. Share it in community chat!')
            return redirect('chat:community')
        else:
            messages.error(request, 'Please enter a valid game code.')
    
    return render(request, 'matches/create_friendly.html')


@login_required
def accept_friendly_match(request, friendly_id):
    friendly = get_object_or_404(FriendlyMatch, id=friendly_id)
    
    player, team, error_resp = require_team(request, func_name="accept friendly match")
    if error_resp:
        return error_resp
    
    if friendly.created_by_team == team:
        messages.error(request, 'You cannot accept your own friendly match.')
        return redirect('chat:community')
    
    if friendly.status == 'open':
        friendly.opponent_team = team
        friendly.status = 'accepted'
        friendly.accepted_at = timezone.now()
        friendly.save()
        messages.success(request, f'Friendly match accepted! Game code: {friendly.game_code}')
    else:
        messages.error(request, 'This friendly match is no longer available.')
    
    return redirect('chat:community')


@staff_member_required
def postponement_approval_queue(request):
    pending_postponements = MatchPostponement.objects.filter(
        status='pending_admin'
    ).select_related('match', 'requested_by', 'match__tournament').order_by('created_at')
    
    return render(request, 'matches/postponement_queue.html', {
        'postponements': pending_postponements
    })


@staff_member_required
def approve_postponement(request, postponement_id):
    postponement = get_object_or_404(MatchPostponement, id=postponement_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            new_date = request.POST.get('new_date')
            new_time = request.POST.get('new_time')
            
            if new_date and new_time:
                postponement.status = 'approved'
                postponement.approved_by = request.user
                postponement.approved_at = timezone.now()
                postponement.save()
                
                match = postponement.match
                match.match_date = new_date
                match.match_time = new_time
                match.save()
                
                messages.success(request, 'Postponement approved and match rescheduled.')
            else:
                messages.error(request, 'Please provide new date and time.')
        
        elif action == 'reject':
            postponement.status = 'rejected'
            postponement.rejection_reason = request.POST.get('reason', 'Rejected by admin')
            postponement.approved_by = request.user
            postponement.approved_at = timezone.now()
            postponement.save()
            
            messages.success(request, 'Postponement rejected.')
        
        return redirect('matches:postponement_queue')
    
    return render(request, 'matches/approve_postponement.html', {
        'postponement': postponement
    })

