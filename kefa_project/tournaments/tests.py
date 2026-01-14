"""
KEFA Tournament Scheduling Tests

Tests for:
- Single/Double Round Robin generation
- Weekday enforcement (League: Thu-Sun, Cup: Mon-Wed)
- Priority-based conflict resolution
- Team availability checking
- Knockout bracket generation and progression
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from kefa_project.tournaments.models import Tournament, TournamentRegistration, Standing
from kefa_project.matches.models import Match
from kefa_project.teams.models import Team
from kefa_project.players.models import Player
from kefa_project.tournaments.services import (
    check_team_availability,
    get_valid_weekday_dates,
    find_next_available_date,
    generate_league_fixtures,
    generate_knockout_fixtures,
    get_bracket_structure
)
from django.contrib.auth.models import User


class RoundRobinGenerationTests(TestCase):
    """Test single and double round robin fixture generation"""
    
    def setUp(self):
        """Create test users, players, and teams"""
        self.teams = []
        for i in range(8):
            user = User.objects.create_user(username=f'user{i}', password='test')
            player = Player.objects.create(user=user, gamertag=f'Player{i}')
            team = Team.objects.create(
                team_name=f'Team {i}',
                player=player,
                team_tag=f'T{i}'
            )
            self.teams.append(team)
    
    def test_single_round_robin_match_count(self):
        """Test that single round robin generates correct number of matches"""
        tournament = Tournament.objects.create(
            name='Test Single RR League',
            tournament_type='league',
            team_limit=8,
            round_robin_type='single',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            status='locked'
        )
        
        # Register teams
        for team in self.teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        # Generate fixtures
        generate_league_fixtures(tournament, self.teams)
        
        # Single round robin: n * (n-1) / 2 = 8 * 7 / 2 = 28 matches
        match_count = Match.objects.filter(tournament=tournament).count()
        self.assertEqual(match_count, 28, f"Expected 28 matches, got {match_count}")
    
    def test_double_round_robin_match_count(self):
        """Test that double round robin generates correct number of matches"""
        tournament = Tournament.objects.create(
            name='Test Double RR League',
            tournament_type='league',
            team_limit=8,
            round_robin_type='double',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=120),
            status='locked'
        )
        
        # Register teams
        for team in self.teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        # Generate fixtures
        generate_league_fixtures(tournament, self.teams)
        
        # Double round robin: n * (n-1) = 8 * 7 = 56 matches
        match_count = Match.objects.filter(tournament=tournament).count()
        self.assertEqual(match_count, 56, f"Expected 56 matches, got {match_count}")
    
    def test_home_away_reversal_in_double_round_robin(self):
        """Test that home/away teams are reversed in second leg"""
        tournament = Tournament.objects.create(
            name='Test Home/Away League',
            tournament_type='league',
            team_limit=4,
            round_robin_type='double',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            status='locked'
        )
        
        test_teams = self.teams[:4]
        for team in test_teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        generate_league_fixtures(tournament, test_teams)
        
        # Find a specific pairing
        team_a = test_teams[0]
        team_b = test_teams[1]
        
        matches = Match.objects.filter(
            tournament=tournament,
            home_team__in=[team_a, team_b],
            away_team__in=[team_a, team_b]
        ).order_by('match_date')
        
        # Should have exactly 2 matches between these teams
        self.assertEqual(matches.count(), 2)
        
        # Home/away should be reversed
        if matches[0].home_team == team_a:
            self.assertEqual(matches[1].home_team, team_b)
            self.assertEqual(matches[1].away_team, team_a)


class WeekdayEnforcementTests(TestCase):
    """Test weekday rules enforcement"""
    
    def setUp(self):
        self.teams = []
        for i in range(4):
            user = User.objects.create_user(username=f'wuser{i}', password='test')
            player = Player.objects.create(user=user, gamertag=f'WPlayer{i}')
            team = Team.objects.create(
                team_name=f'WTeam {i}',
                player=player,
                team_tag=f'WT{i}'
            )
            self.teams.append(team)
    
    def test_league_matches_on_correct_weekdays(self):
        """Test that league matches are only scheduled on Thu-Sun"""
        tournament = Tournament.objects.create(
            name='Test League Weekdays',
            tournament_type='league',
            team_limit=4,
            round_robin_type='single',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='locked'
        )
        
        for team in self.teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        generate_league_fixtures(tournament, self.teams)
        
        # Check all matches are on Thu-Sun (weekdays 3,4,5,6)
        matches = Match.objects.filter(tournament=tournament)
        for match in matches:
            weekday = match.match_date.weekday()
            self.assertIn(weekday, [3, 4, 5, 6], 
                f"League match on {match.match_date} is on weekday {weekday}, expected Thu-Sun (3-6)")
    
    def test_cup_matches_on_correct_weekdays(self):
        """Test that cup matches are only scheduled on Mon-Wed"""
        tournament = Tournament.objects.create(
            name='Test Cup Weekdays',
            tournament_type='knockout',
            team_limit=4,
            start_date=date.today(),
            status='locked'
        )
        
        for team in self.teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        generate_knockout_fixtures(tournament, self.teams)
        
        # Check all matches are on Mon-Wed (weekdays 0,1,2)
        matches = Match.objects.filter(tournament=tournament)
        for match in matches:
            weekday = match.match_date.weekday()
            self.assertIn(weekday, [0, 1, 2], 
                f"Cup match on {match.match_date} is on weekday {weekday}, expected Mon-Wed (0-2)")


class TeamAvailabilityTests(TestCase):
    """Test team availability checking and conflict detection"""
    
    def setUp(self):
        user = User.objects.create_user(username='avail_user', password='test')
        player = Player.objects.create(user=user, gamertag='AvailPlayer')
        self.team = Team.objects.create(
            team_name='Availability Team',
            player=player,
            team_tag='AT'
        )
        
        user2 = User.objects.create_user(username='avail_user2', password='test')
        player2 = Player.objects.create(user=user2, gamertag='AvailPlayer2')
        self.team2 = Team.objects.create(
            team_name='Availability Team 2',
            player=player2,
            team_tag='AT2'
        )
    
    def test_team_availability_with_existing_match(self):
        """Test that team is marked unavailable when it has a match"""
        tournament = Tournament.objects.create(
            name='Test Tournament',
            tournament_type='league',
            team_limit=4,
            start_date=date.today(),
            status='locked'
        )
        
        test_date = date.today() + timedelta(days=5)
        
        # Create a match for the team
        Match.objects.create(
            tournament=tournament,
            home_team=self.team,
            away_team=self.team2,
            match_date=test_date,
            match_time='17:00:00',
            status='scheduled'
        )
        
        # Check availability
        is_available, blocking_match = check_team_availability(self.team, test_date)
        
        self.assertFalse(is_available, "Team should be unavailable")
        self.assertIsNotNone(blocking_match, "Blocking match should be returned")
    
    def test_team_availability_without_match(self):
        """Test that team is available when it has no match"""
        test_date = date.today() + timedelta(days=10)
        
        is_available, blocking_match = check_team_availability(self.team, test_date)
        
        self.assertTrue(is_available, "Team should be available")
        self.assertIsNone(blocking_match, "No blocking match should exist")


class PrioritySchedulingTests(TestCase):
    """Test priority-based conflict resolution"""
    
    def setUp(self):
        self.teams = []
        for i in range(4):
            user = User.objects.create_user(username=f'puser{i}', password='test')
            player = Player.objects.create(user=user, gamertag=f'PPlayer{i}')
            team = Team.objects.create(
                team_name=f'PTeam {i}',
                player=player,
                team_tag=f'PT{i}'
            )
            self.teams.append(team)
    
    def test_higher_priority_blocks_lower_priority(self):
        """Test that higher priority tournament blocks dates for lower priority"""
        # Create Champions Cup (priority 1)
        champions_cup = Tournament.objects.create(
            name='Champions Cup',
            tournament_type='champions_league',
            team_limit=4,
            priority=1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='locked'
        )
        
        # Create League (priority 3)
        league = Tournament.objects.create(
            name='Test League',
            tournament_type='league',
            team_limit=4,
            priority=3,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status='locked'
        )
        
        test_date = date.today() + timedelta(days=5)
        
        # Create Champions Cup match
        Match.objects.create(
            tournament=champions_cup,
            home_team=self.teams[0],
            away_team=self.teams[1],
            match_date=test_date,
            match_time='17:00:00',
            status='scheduled'
        )
        
        # Check if team is available for league match (priority 3)
        is_available, blocking_match = check_team_availability(
            self.teams[0], 
            test_date, 
            tournament_priority=3
        )
        
        self.assertFalse(is_available, "Team should be blocked by higher priority match")
        self.assertEqual(blocking_match.tournament, champions_cup)


class KnockoutBracketTests(TestCase):
    """Test knockout bracket generation and progression"""
    
    def setUp(self):
        self.teams = []
        for i in range(8):
            user = User.objects.create_user(username=f'kuser{i}', password='test')
            player = Player.objects.create(user=user, gamertag=f'KPlayer{i}')
            team = Team.objects.create(
                team_name=f'KTeam {i}',
                player=player,
                team_tag=f'KT{i}'
            )
            self.teams.append(team)
    
    def test_knockout_bracket_structure_8_teams(self):
        """Test that 8-team bracket creates correct structure"""
        tournament = Tournament.objects.create(
            name='Test Knockout',
            tournament_type='knockout',
            team_limit=8,
            start_date=date.today(),
            status='locked'
        )
        
        for team in self.teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        generate_knockout_fixtures(tournament, self.teams)
        
        # 8 teams: QF(4) + SF(2) + F(1) = 7 matches
        total_matches = Match.objects.filter(tournament=tournament).count()
        self.assertEqual(total_matches, 7)
        
        # Check round distribution
        qf_matches = Match.objects.filter(tournament=tournament, knockout_round='quarter_final').count()
        sf_matches = Match.objects.filter(tournament=tournament, knockout_round='semi_final').count()
        final_matches = Match.objects.filter(tournament=tournament, knockout_round='final').count()
        
        self.assertEqual(qf_matches, 4, "Should have 4 quarter-finals")
        self.assertEqual(sf_matches, 2, "Should have 2 semi-finals")
        self.assertEqual(final_matches, 1, "Should have 1 final")
    
    def test_winner_advancement(self):
        """Test that match winner advances to next round"""
        tournament = Tournament.objects.create(
            name='Test Winner Advancement',
            tournament_type='knockout',
            team_limit=4,
            start_date=date.today(),
            status='locked'
        )
        
        test_teams = self.teams[:4]
        for team in test_teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        generate_knockout_fixtures(tournament, test_teams)
        
        # Get a semi-final match
        sf_match = Match.objects.filter(
            tournament=tournament,
            knockout_round='semi_final'
        ).first()
        
        # Complete the match
        sf_match.home_score = 3
        sf_match.away_score = 1
        sf_match.status = 'completed'
        sf_match.save()
        
        # Advance winner
        sf_match.advance_winner()
        
        # Check that winner is in final
        final_match = sf_match.next_match
        self.assertIsNotNone(final_match)
        self.assertIn(sf_match.home_team, [final_match.home_team, final_match.away_team])
    
    def test_bracket_data_structure(self):
        """Test that bracket data structure is correctly formatted"""
        tournament = Tournament.objects.create(
            name='Test Bracket Data',
            tournament_type='knockout',
            team_limit=4,
            start_date=date.today(),
            status='locked'
        )
        
        test_teams = self.teams[:4]
        for team in test_teams:
            TournamentRegistration.objects.create(
                tournament=tournament,
                team=team,
                payment_verified=True
            )
        
        generate_knockout_fixtures(tournament, test_teams)
        
        bracket_data = get_bracket_structure(tournament)
        
        # Check structure
        self.assertIn('rounds', bracket_data)
        self.assertIn('total_rounds', bracket_data)
        self.assertGreater(bracket_data['total_rounds'], 0)
        
        # Check round data
        for round_data in bracket_data['rounds']:
            self.assertIn('name', round_data)
            self.assertIn('display_name', round_data)
            self.assertIn('matches', round_data)
            
            # Check match data
            for match_data in round_data['matches']:
                self.assertIn('home_team', match_data)
                self.assertIn('away_team', match_data)
                self.assertIn('status', match_data)


class HelperFunctionTests(TestCase):
    """Test scheduling helper functions"""
    
    def test_get_valid_weekday_dates(self):
        """Test weekday date filtering"""
        start = date(2026, 1, 20)  # Monday
        end = date(2026, 1, 26)    # Sunday
        
        # Get only Mon-Wed (0,1,2)
        valid_dates = get_valid_weekday_dates(start, end, [0, 1, 2], frequency_days=1)
        
        for d in valid_dates:
            self.assertIn(d.weekday(), [0, 1, 2])
        
        # Should have Mon, Tue, Wed from that week
        self.assertGreaterEqual(len(valid_dates), 3)
    
    def test_get_valid_weekday_dates_with_frequency(self):
        """Test weekday filtering with frequency constraint"""
        start = date(2026, 1, 22)  # Thursday
        end = date(2026, 2, 5)     # 2 weeks later
        
        # Get Thu-Sun with 3-day frequency
        valid_dates = get_valid_weekday_dates(start, end, [3, 4, 5, 6], frequency_days=3)
        
        # Check all dates are on correct weekdays
        for d in valid_dates:
            self.assertIn(d.weekday(), [3, 4, 5, 6])
        
        # Check frequency constraint
        for i in range(1, len(valid_dates)):
            days_diff = (valid_dates[i] - valid_dates[i-1]).days
            self.assertGreaterEqual(days_diff, 3)


# Run tests with: python manage.py test kefa_project.tournaments.tests
