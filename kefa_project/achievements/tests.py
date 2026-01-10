from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.matches.models import Match
from kefa_project.tournaments.models import Tournament
from kefa_project.achievements.models import Badge, PlayerBadge
from kefa_project.achievements.services import calculate_player_of_the_week, check_match_milestones

class AchievementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testplayer', password='password')
        self.player = Player.objects.create(user=self.user, full_name='Test Player')
        self.team = Team.objects.create(player=self.player, team_name='Test FC')
        
        self.opponent_user = User.objects.create_user(username='opponent', password='password')
        self.opponent_player = Player.objects.create(user=self.opponent_user, full_name='Opponent')
        self.opponent_team = Team.objects.create(player=self.opponent_player, team_name='Opponent FC')

        self.tournament = Tournament.objects.create(
            name='Test Cup', tournament_type='knockout', 
            team_limit=4, start_date=timezone.now().date()
        )

    def test_milestone_first_match_and_win(self):
        """Test First Match and First Win milestones"""
        # Create a completed match won by our team
        Match.objects.create(
            tournament=self.tournament,
            home_team=self.team,
            away_team=self.opponent_team,
            match_date=timezone.now().date(),
            match_time=timezone.now().time(),
            status='completed',
            home_score=3,
            away_score=1
        )
        
        check_match_milestones(self.team)
        
        self.assertTrue(PlayerBadge.objects.filter(player=self.player, badge__name='First Match Played').exists())
        self.assertTrue(PlayerBadge.objects.filter(player=self.player, badge__name='First Victory').exists())

    def test_player_of_week_calculation(self):
        """Test core logic for Player of the Week"""
        # Create a match 2 days ago where our team won big
        Match.objects.create(
            tournament=self.tournament,
            home_team=self.team,
            away_team=self.opponent_team,
            match_date=timezone.now().date() - timedelta(days=2),
            match_time=timezone.now().time(),
            status='completed',
            home_score=5,
            away_score=0
        )
        
        winner = calculate_player_of_the_week()
        
        self.assertIsNotNone(winner)
        self.assertEqual(winner, self.player)
        self.assertTrue(PlayerBadge.objects.filter(player=self.player, badge__badge_type='player_of_week').exists())
