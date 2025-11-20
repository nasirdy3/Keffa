from django.db.models import Sum, Q
from django.utils import timezone
from .models import Badge, PlayerBadge, Trophy
from kefa_project.tournaments.models import Tournament, Standing
from kefa_project.matches.models import Match


def award_automatic_achievements(tournament):
    if tournament.status != 'completed':
        return
    
    standings = Standing.objects.filter(tournament=tournament).order_by('-points', '-goal_difference')
    
    if standings.count() == 0:
        return
    
    winner_standing = standings.first()
    winner_team = winner_standing.team
    winner_player = winner_team.player
    
    winner_badge, _ = Badge.objects.get_or_create(
        badge_type='tournament_winner',
        defaults={
            'name': 'Tournament Winner',
            'description': 'Won a tournament',
            'is_automatic': True
        }
    )
    
    PlayerBadge.objects.get_or_create(
        player=winner_player,
        badge=winner_badge,
        tournament=tournament,
        defaults={'notes': f'Won {tournament.name}'}
    )
    
    Trophy.objects.get_or_create(
        team=winner_team,
        tournament=tournament,
        defaults={
            'trophy_type': 'gold',
            'position': 1
        }
    )
    
    if standings.count() >= 2:
        runner_up_standing = standings[1]
        runner_up_team = runner_up_standing.team
        runner_up_player = runner_up_team.player
        
        runner_up_badge, _ = Badge.objects.get_or_create(
            badge_type='runner_up',
            defaults={
                'name': 'Runner-Up',
                'description': 'Finished second in a tournament',
                'is_automatic': True
            }
        )
        
        PlayerBadge.objects.get_or_create(
            player=runner_up_player,
            badge=runner_up_badge,
            tournament=tournament,
            defaults={'notes': f'Runner-up in {tournament.name}'}
        )
        
        Trophy.objects.get_or_create(
            team=runner_up_team,
            tournament=tournament,
            defaults={
                'trophy_type': 'silver',
                'position': 2
            }
        )
    
    if standings.count() >= 3:
        third_place_standing = standings[2]
        third_place_team = third_place_standing.team
        
        Trophy.objects.get_or_create(
            team=third_place_team,
            tournament=tournament,
            defaults={
                'trophy_type': 'bronze',
                'position': 3
            }
        )
    
    top_scorer_team = standings.order_by('-goals_for').first()
    if top_scorer_team:
        top_scorer_player = top_scorer_team.team.player
        
        top_scorer_badge, _ = Badge.objects.get_or_create(
            badge_type='top_scorer',
            defaults={
                'name': 'Top Scorer',
                'description': 'Highest goals in a tournament',
                'is_automatic': True
            }
        )
        
        PlayerBadge.objects.get_or_create(
            player=top_scorer_player,
            badge=top_scorer_badge,
            tournament=tournament,
            defaults={'notes': f'Top scorer in {tournament.name} with {top_scorer_team.goals_for} goals'}
        )


def award_manual_badge(player, badge_type, tournament=None, awarded_by=None, notes=''):
    badge = Badge.objects.filter(badge_type=badge_type).first()
    
    if not badge:
        return None
    
    player_badge, created = PlayerBadge.objects.get_or_create(
        player=player,
        badge=badge,
        tournament=tournament,
        defaults={
            'awarded_by': awarded_by,
            'notes': notes
        }
    )
    
    return player_badge if created else None
