from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from .models import Match, MatchPostponement, FriendlyMatch
from kefa_project.teams.models import Team


@login_required
def match_ready(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team to mark ready.')
        return redirect('players:player_dashboard')
    
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
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team.')
        return redirect('players:player_dashboard')
    
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
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team.')
        return redirect('players:player_dashboard')
    
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
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team.')
        return redirect('players:player_dashboard')
    
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
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team to create a friendly match.')
        return redirect('players:player_dashboard')
    
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
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team.')
        return redirect('players:player_dashboard')
    
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


@staff_member_required
def verification_queue(request):
    """Admin view to see matches pending result verification."""
    # Matches that are marked as 'pending_verification' or disputed.
    # Currently strictly filtering by 'pending_verification' status.
    pending_matches = Match.objects.filter(
        status='pending_verification'
    ).select_related('tournament', 'home_team', 'away_team').order_by('match_date')
    
    return render(request, 'matches/verification_queue.html', {
        'matches': pending_matches
    })


@staff_member_required
def verify_match_result(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            home_score = request.POST.get('home_score')
            away_score = request.POST.get('away_score')
            
            if home_score is not None and away_score is not None:
                match.home_score = int(home_score)
                match.away_score = int(away_score)
                match.status = 'completed'
                match.verified_at = timezone.now()
                match.verified_by = request.user
                match.save()
                
                # Update standings
                from kefa_project.tournaments.services import update_standings
                update_standings(match)
                
                messages.success(request, f"Match {match} verified as {home_score}-{away_score}.")
            else:
                messages.error(request, 'Scores are required for verification.')
        
        elif action == 'cancel':
            # Optionally reset to in_progress or another status
            match.status = 'in_progress'
            match.save()
            messages.info(request, "Match status reverted to In Progress.")
            
        return redirect('matches:verification_queue')
        
    return redirect('matches:verification_queue')


@login_required
def match_detail(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    return render(request, 'matches/match_detail.html', {'match': match})
