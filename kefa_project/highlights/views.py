from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Highlight
from kefa_project.matches.models import Match
from kefa_project.tournaments.services import update_standings_after_match
from kefa_project.achievements.services import award_automatic_achievements


@login_required
def upload_highlight(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    try:
        player = request.user.player_profile
        team = player.team
    except:
        messages.error(request, 'You must have a team to upload highlights.')
        return redirect('players:player_dashboard')

    # Chapter 7 Regulation: Only Home Team can upload
    if match.home_team != team:
        messages.error(request, 'Regulation: Only the Home Team is permitted to upload match evidence.')
        return redirect('players:player_dashboard')

    # Chapter 7 Time Regulation: "Upload window opens 15 minutes after match start"
    match_start_dt = timezone.make_aware(
        timezone.datetime.combine(match.match_date, match.match_time),
        timezone.get_current_timezone()
    )
    time_since_start = (timezone.now() - match_start_dt).total_seconds()
    
    if time_since_start < 900: # 15 minutes * 60 seconds = 900
        wait_min = int((900 - time_since_start) / 60)
        messages.error(request, f'Regulation: Upload window opens 15 minutes after match start. Please wait {wait_min} more minutes.')
        return redirect('players:player_dashboard')
    
    uploaded_by_side = 'home'
    
    # Check if a pending highlight already exists to prevent duplicates
    existing_highlight = Highlight.objects.filter(
        match=match,
        uploaded_by_team=team,
        status='pending_verification'
    ).first()
    
    if existing_highlight:
        messages.warning(request, 'You have already uploaded a highlight. Please wait for verification.')
        return redirect('players:player_dashboard')
    
    if request.method == 'POST':
        # ARCHITECT FIX: Handle FILES and POST data separately
        video_url = request.POST.get('video_url', '').strip()
        description = request.POST.get('description', '')
        
        video_file = request.FILES.get('video_file')
        evidence_screenshot = request.FILES.get('evidence_screenshot')
        
        # Validation: Must have at least one form of evidence
        if not any([video_url, video_file, evidence_screenshot]):
            messages.error(request, 'You must provide a Video File, a Screenshot, or a Video URL.')
        else:
            highlight = Highlight.objects.create(
                match=match,
                uploaded_by_team=team,
                uploaded_by_side=uploaded_by_side,
                video_url=video_url if video_url else None,
                video_file=video_file,
                evidence_screenshot=evidence_screenshot,
                description=description,
                status='pending_verification'
            )
            
            match.status = 'pending_verification'
            match.save()
            
            messages.success(request, 'Evidence uploaded successfully! It will be verified by moderators soon.')
            return redirect('players:player_dashboard')
    
    return render(request, 'highlights/upload.html', {'match': match})


@staff_member_required
def verification_queue(request):
    pending_highlights = Highlight.objects.filter(
        status='pending_verification'
    ).select_related('match', 'uploaded_by_team', 'match__tournament').order_by('uploaded_at')
    
    return render(request, 'highlights/verification_queue.html', {
        'highlights': pending_highlights
    })


@staff_member_required
def verify_highlight(request, highlight_id):
    highlight = get_object_or_404(Highlight, id=highlight_id)
    match = highlight.match
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            home_score = request.POST.get('home_score')
            away_score = request.POST.get('away_score')
            
            if home_score and away_score:
                with transaction.atomic():
                    highlight.status = 'verified'
                    highlight.verified_by = request.user
                    highlight.verified_at = timezone.now()
                    highlight.save()
                    
                    match.home_score = int(home_score)
                    match.away_score = int(away_score)
                    match.status = 'completed'
                    match.verified_at = timezone.now()
                    match.verified_by = request.user
                    match.save()
                    
                    # Update Standings
                    try:
                        update_standings_after_match(match)
                    except Exception as e:
                        print(f"Error updating standings: {e}")
                    
                    # Award Achievements
                    try:
                        award_automatic_achievements(match.tournament)
                    except Exception as e:
                        print(f"Error awarding achievements: {e}")
                    
                messages.success(request, f'Match verified! Score: {home_score}-{away_score}')
                return redirect('highlights:verification_queue')
            else:
                messages.error(request, 'Please enter both scores.')
        
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            
            highlight.status = 'rejected'
            highlight.rejection_reason = rejection_reason
            highlight.verified_by = request.user
            highlight.verified_at = timezone.now()
            highlight.save()
            
            match.status = 'awaiting_highlight' # Reset match status so they can upload again
            match.save()
            
            messages.success(request, 'Highlight rejected. User can now upload new evidence.')
            return redirect('highlights:verification_queue')
        
    return render(request, 'highlights/verify.html', {
        'highlight': highlight,
        'match': match
    })


def public_highlights(request):
    verified_highlights = Highlight.objects.filter(
        status='verified'
    ).select_related('match', 'uploaded_by_team', 'match__tournament').order_by('-verified_at')[:50]
    
    return render(request, 'highlights/gallery.html', {
        'highlights': verified_highlights
    })

