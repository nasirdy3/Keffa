from django.shortcuts import render
from django.db.models import Count, Sum
from django.contrib.admin.views.decorators import staff_member_required
from kefa_project.tournaments.models import Tournament, Standing
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.matches.models import Match
from kefa_project.highlights.models import Highlight
from kefa_project.payments.models import Payment


def home(request):
    """Homepage view with platform statistics"""
    
    # Get statistics
    total_players = Player.objects.count()
    total_teams = Team.objects.count()
    active_tournaments = Tournament.objects.filter(
        status__in=['registration', 'locked', 'ongoing']
    ).count()
    total_matches = Match.objects.filter(status='completed').count()
    
    # Get featured tournaments (active ones)
    featured_tournaments = Tournament.objects.filter(
        status__in=['registration', 'ongoing']
    ).order_by('-created_at')[:3]
    
    context = {
        'total_players': total_players,
        'total_teams': total_teams,
        'active_tournaments': active_tournaments,
        'total_matches': total_matches,
        'featured_tournaments': featured_tournaments,
    }
    
    return render(request, 'home.html', context)


@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with all key metrics and quick actions"""
    
    # Verification queues
    pending_payments = Payment.objects.filter(
        payment_method='offline',
        status='pending'
    ).count()
    
    pending_highlights = Highlight.objects.filter(
        status='pending_verification'
    ).count()
    
    # Platform stats
    total_players = Player.objects.count()
    total_teams = Team.objects.count()
    active_tournaments = Tournament.objects.filter(
        status__in=['registration', 'locked', 'ongoing']
    ).count()
    total_matches = Match.objects.filter(status='completed').count()
    verified_highlights = Highlight.objects.filter(status='verified').count()
    
    # Revenue stats
    total_revenue = Payment.objects.filter(
        status='verified'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent tournaments
    recent_tournaments = Tournament.objects.all().order_by('-created_at')[:5]
    
    context = {
        'pending_payments': pending_payments,
        'pending_highlights': pending_highlights,
        'total_players': total_players,
        'total_teams': total_teams,
        'active_tournaments': active_tournaments,
        'total_matches': total_matches,
        'verified_highlights': verified_highlights,
        'total_revenue': total_revenue,
        'recent_tournaments': recent_tournaments,
    }
    
    return render(request, 'admin/dashboard.html', context)


def leaderboards(request):
    """Leaderboards showing top teams and top scorers"""
    
    top_teams = Standing.objects.select_related('team', 'tournament').order_by('-points', '-goals_for')[:20]
    
    top_scorers = Standing.objects.select_related('team__player', 'tournament').filter(
        goals_for__gt=0
    ).order_by('-goals_for')[:20]
    
    top_players = Player.objects.annotate(
        achievements_count=Count('badges')
    ).filter(achievements_count__gt=0).order_by('-achievements_count')[:20]
    
    context = {
        'top_teams': top_teams,
        'top_scorers': top_scorers,
        'top_players': top_players,
    }
    
    return render(request, 'leaderboards.html', context)
