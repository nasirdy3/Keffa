from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Match
from kefa_project.tournaments.models import Standing


@shared_task
def check_match_ready_windows():
    now = timezone.now()
    
    scheduled_matches = Match.objects.filter(
        status='scheduled'
    )
    
    for match in scheduled_matches:
        match_datetime = timezone.make_aware(
            timezone.datetime.combine(match.match_date, match.match_time),
            timezone.get_current_timezone()
        )
        
        time_until_match = (match_datetime - now).total_seconds()
        
        if -300 <= time_until_match <= 300:
            if not match.ready_time_start:
                match.status = 'ready_pending'
                match.ready_time_start = now
                match.save()
    
    ready_pending_matches = Match.objects.filter(
        status='ready_pending',
        ready_time_start__isnull=False
    )
    
    for match in ready_pending_matches:
        time_since_ready = (now - match.ready_time_start).total_seconds()
        
        if time_since_ready > 300:
            from django.db import transaction
            with transaction.atomic():
                match_locked = Match.objects.select_for_update().get(id=match.id)
                
                if match_locked.status != 'ready_pending':
                    continue
                
                if match_locked.home_ready and match_locked.away_ready:
                    match_locked.status = 'creating_game'
                    match_locked.save()
                elif match_locked.home_ready and not match_locked.away_ready:
                    match_locked.status = 'away_forfeit'
                    match_locked.away_score = 0
                    match_locked.home_score = 3
                    match_locked.verified_at = now
                    match_locked.save()
                    update_standings_on_forfeit(match_locked, 'away')
                elif not match_locked.home_ready and match_locked.away_ready:
                    match_locked.status = 'home_forfeit'
                    match_locked.home_score = 0
                    match_locked.away_score = 3
                    match_locked.verified_at = now
                    match_locked.save()
                    update_standings_on_forfeit(match_locked, 'home')
                else:
                    match_locked.status = 'both_forfeit'
                    match_locked.home_score = 0
                    match_locked.away_score = 0
                    match_locked.verified_at = now
                    match_locked.save()
    
    creating_game_matches = Match.objects.filter(
        status='creating_game',
        ready_time_start__isnull=False
    )
    
    for match in creating_game_matches:
        time_since_ready = (now - match.ready_time_start).total_seconds()
        
        if time_since_ready > 600 and not match.game_code:
            from django.db import transaction
            with transaction.atomic():
                match_locked = Match.objects.select_for_update().get(id=match.id)
                
                if match_locked.status != 'creating_game' or match_locked.game_code:
                    continue
                
                match_locked.status = 'home_forfeit'
                match_locked.home_score = 0
                match_locked.away_score = 3
                match_locked.verified_at = now
                match_locked.save()
                update_standings_on_forfeit(match_locked, 'home')
    
    waiting_join_matches = Match.objects.filter(
        status='waiting_join',
        game_code_created_at__isnull=False
    )
    
    for match in waiting_join_matches:
        time_since_code = (now - match.game_code_created_at).total_seconds()
        
        if time_since_code > 300:
            from django.db import transaction
            with transaction.atomic():
                match_locked = Match.objects.select_for_update().get(id=match.id)
                
                if match_locked.status != 'waiting_join':
                    continue
                
                match_locked.status = 'away_forfeit'
                match_locked.home_score = 3
                match_locked.away_score = 0
                match_locked.verified_at = now
                match_locked.save()
                update_standings_on_forfeit(match_locked, 'away')


@shared_task
def check_highlight_deadlines():
    now = timezone.now()
    cutoff_time = now - timedelta(hours=24)
    
    matches = Match.objects.filter(
        status='awaiting_highlight'
    )
    
    for match in matches:
        match_datetime = timezone.make_aware(
            timezone.datetime.combine(match.match_date, match.match_time),
            timezone.get_current_timezone()
        )
        
        if match_datetime < cutoff_time:
            from django.db import transaction
            with transaction.atomic():
                match_locked = Match.objects.select_for_update().get(id=match.id)
                
                if match_locked.status != 'awaiting_highlight':
                    continue
                
                has_home_highlight = match_locked.highlights.filter(uploaded_by_side='home').exists()
                has_away_highlight = match_locked.highlights.filter(uploaded_by_side='away').exists()
                
                if not has_home_highlight and not has_away_highlight:
                    apply_penalty(match_locked.tournament, match_locked.home_team)
                    apply_penalty(match_locked.tournament, match_locked.away_team)
                    
                    match_locked.status = 'both_forfeit'
                    match_locked.home_score = 0
                    match_locked.away_score = 0
                    match_locked.save()


def apply_penalty(tournament, team):
    try:
        standing = Standing.objects.get(tournament=tournament, team=team)
        standing.points = max(0, standing.points - 1)
        standing.save()
    except Standing.DoesNotExist:
        pass


def update_standings_on_forfeit(match, forfeiting_team):
    from kefa_project.tournaments.services import update_standings_after_match
    match.status = 'completed'
    match.save()
    update_standings_after_match(match)
