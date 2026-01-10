from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from kefa_project.players.models import Player
from kefa_project.teams.models import Team
from kefa_project.tournaments.models import Tournament, TournamentRegistration, Standing
from kefa_project.matches.models import Match
from kefa_project.achievements.models import Badge, PlayerBadge, Trophy
from kefa_project.tournaments.services import lock_and_generate_fixtures, process_season_end

class TournamentAutomationTests(TestCase):
    def setUp(self):
        # Create Users & Players
        self.user1 = User.objects.create_user(username='player1', password='password')
        self.player1 = Player.objects.create(user=self.user1, full_name='Player One', phone_number='1234567890')
        
        self.user2 = User.objects.create_user(username='player2', password='password')
        self.player2 = Player.objects.create(user=self.user2, full_name='Player Two', phone_number='0987654321')
        
        self.user3 = User.objects.create_user(username='player3', password='password')
        self.player3 = Player.objects.create(user=self.user3, full_name='Player Three', phone_number='1122334455')
        
        # Create Teams
        self.team1 = Team.objects.create(player=self.player1, team_name='Team Alpha', team_logo='logo.png')
        self.team2 = Team.objects.create(player=self.player2, team_name='Team Beta', team_logo='logo.png')
        self.team3 = Team.objects.create(player=self.player3, team_name='Team Gamma', team_logo='logo.png')
        
        # Create Badges Types
        Badge.objects.create(name='Winner', badge_type='tournament_winner', description='Won a tournament')
        Badge.objects.create(name='Runner Up', badge_type='runner_up', description='Runner up')
        
        # Create Tournament
        self.tournament = Tournament.objects.create(
            name='Test League',
            tournament_type='league',
            team_limit=4,
            start_date=timezone.now().date(),
            match_frequency='daily'
        )
        
        # Register Teams
        TournamentRegistration.objects.create(tournament=self.tournament, team=self.team1, payment_verified=True)
        TournamentRegistration.objects.create(tournament=self.tournament, team=self.team2, payment_verified=True)
        TournamentRegistration.objects.create(tournament=self.tournament, team=self.team3, payment_verified=True)

    def test_fixture_generation_league(self):
        """Test that league fixtures are generated correctly (Double Round Robin)"""
        # 3 Teams -> 6 Matches per team against each other? 
        # With 3 teams: 
        # Round 1: 1v2, 3 Bye
        # Round 2: ...
        # Total matches for 3 teams double RR = 3 * 2 = 6 matches total.
        
        lock_and_generate_fixtures(self.tournament)
        
        matches_count = Match.objects.filter(tournament=self.tournament).count()
        self.assertEqual(matches_count, 6)
        
        # Verify Standings created
        standings_count = Standing.objects.filter(tournament=self.tournament).count()
        self.assertEqual(standings_count, 3)

    def test_season_end_processing(self):
        """Test that season end awards trophies and badges correctly"""
        # Manually create standings
        Standing.objects.create(tournament=self.tournament, team=self.team1, points=10, goals_for=5) # 1st
        Standing.objects.create(tournament=self.tournament, team=self.team2, points=8, goals_for=3)  # 2nd
        Standing.objects.create(tournament=self.tournament, team=self.team3, points=5, goals_for=1)  # 3rd
        
        # Call process season end
        success, message = process_season_end(self.tournament)
        
        self.assertTrue(success)
        self.assertEqual(self.tournament.status, 'completed')
        
        # Verify Trophies
        self.assertTrue(Trophy.objects.filter(tournament=self.tournament, team=self.team1, trophy_type='gold').exists())
        self.assertTrue(Trophy.objects.filter(tournament=self.tournament, team=self.team2, trophy_type='silver').exists())
        self.assertTrue(Trophy.objects.filter(tournament=self.tournament, team=self.team3, trophy_type='bronze').exists())
        
        # Verify Badges
        self.assertTrue(PlayerBadge.objects.filter(player=self.player1, badge__badge_type='tournament_winner').exists())
        self.assertTrue(PlayerBadge.objects.filter(player=self.player2, badge__badge_type='runner_up').exists())
