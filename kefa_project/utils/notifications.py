from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_tournament_notification(tournament, subject, message, recipient_emails=None):
    """
    Send email notification to tournament participants
    """
    if not recipient_emails:
        from kefa_project.tournaments.models import TournamentRegistration
        registrations = TournamentRegistration.objects.filter(
            tournament=tournament,
            payment_verified=True
        ).select_related('team__player__user')
        
        recipient_emails = [
            reg.team.player.user.email 
            for reg in registrations 
            if reg.team.player.user.email
        ]
    
    if not recipient_emails:
        return
    
    try:
        send_mail(
            subject=f'[KEFA] {subject}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_match_notification(match, subject, message):
    """
    Send email notification to both teams in a match
    """
    recipient_emails = []
    
    if match.home_team and match.home_team.player and match.home_team.player.user.email:
        recipient_emails.append(match.home_team.player.user.email)
    
    if match.away_team and match.away_team.player and match.away_team.player.user.email:
        recipient_emails.append(match.away_team.player.user.email)
    
    if not recipient_emails:
        return
    
    try:
        send_mail(
            subject=f'[KEFA] {subject}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_achievement_notification(player, achievement_name):
    """
    Send email notification when player earns an achievement
    """
    if not player.user.email:
        return
    
    subject = f'Achievement Unlocked: {achievement_name}'
    message = f"""
Congratulations {player.full_name}!

You've unlocked a new achievement: {achievement_name}

Keep up the great performance in KEFA!

Visit your dashboard to see all your achievements.
    """
    
    try:
        send_mail(
            subject=f'[KEFA] {subject}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[player.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_payment_confirmation(registration):
    """
    Send payment confirmation email
    """
    if not registration.team.player.user.email:
        return
    
    subject = f'Payment Confirmed - {registration.tournament.name}'
    message = f"""
Hello {registration.team.player.full_name}!

Your payment for {registration.tournament.name} has been confirmed.

Team: {registration.team.team_name}
Entry Fee: ₦{registration.tournament.registration_fee}
Start Date: {registration.tournament.start_date}

You are now officially registered! Good luck in the tournament!
    """
    
    try:
        send_mail(
            subject=f'[KEFA] {subject}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.team.player.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
