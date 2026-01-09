import random
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction
from .models import Tournament, TournamentRegistration, Standing
from kefa_project.matches.models import Match


def get_randomized_match_time(default_time):
    """
    Returns a randomized match time with 70-80% at default (usually 5 PM)
    and the rest distributed among other valid times (3 PM, 4 PM, 6 PM, 7 PM)
    """
    random_choice = random.random()
    
    if random_choice < 0.75:
        return default_time
    
    other_times = [
        time(15, 0),
        time(16, 0),
        time(18, 0),
        time(19, 0),
    ]
    
    return random.choice(other_times)


def lock_and_generate_fixtures(tournament):
    """
    Initial generation of fixtures when tournament fills up or is manually locked.
    """
    verified_registrations = tournament.registrations.filter(payment_verified=True).select_related('team')
    teams = [reg.team for reg in verified_registrations]
    
    if len(teams) < 2:
        return
    
    # Initialize Standings
    for team in teams:
        Standing.objects.get_or_create(
            tournament=tournament,
            team=team,
            defaults={
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goals_for': 0, 'goals_against': 0, 'points': 0, 'form': '',
            }
        )
    
    # Route to specific generation logic
    if tournament.tournament_type in ['league', 'champions_league']:
        generate_league_fixtures(tournament, teams)
    elif tournament.tournament_type == 'knockout':
        generate_knockout_fixtures(tournament, teams)
    elif tournament.tournament_type == 'group_stage':
        generate_group_stage_fixtures(tournament, teams)


def regenerate_fixtures(tournament):
    """
    Regenerates fixtures only if no matches have started.
    Useful if a team drops out or is replaced before the season starts.
    """
    verified_registrations = tournament.registrations.filter(payment_verified=True).select_related('team')
    teams = [reg.team for reg in verified_registrations]
    
    if len(teams) < 2:
        return
    
    # Safety Check: Do not nuke fixtures if the tournament has active gameplay
    any_matches_started = Match.objects.filter(
        tournament=tournament
    ).exclude(status='scheduled').exists()
    
    if any_matches_started:
        return
    
    # Clear existing unplayed matches
    Match.objects.filter(tournament=tournament, status='scheduled').delete()
    
    # Ensure standings exist (in case of new teams)
    for team in teams:
        Standing.objects.get_or_create(
            tournament=tournament,
            team=team,
            defaults={
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goals_for': 0, 'goals_against': 0, 'points': 0, 'form': '',
            }
        )
    
    if tournament.tournament_type in ['league', 'champions_league']:
        generate_league_fixtures(tournament, teams)
    elif tournament.tournament_type == 'knockout':
        generate_knockout_fixtures(tournament, teams)
    elif tournament.tournament_type == 'group_stage':
        generate_group_stage_fixtures(tournament, teams)


def generate_league_fixtures(tournament, teams):
    """
    Implements a Double Round-Robin Algorithm with Intelligent Date Distribution.
    
    Key Features:
    1. Distributes matches evenly across the entire tournament date range
    2. Respects match_frequency setting (daily, every 2 days, etc.)
    3. Ensures no matches are scheduled beyond end_date
    4. Handles odd number of teams with bye weeks
    5. Maintains proper home/away balance
    """
    
    # 1. Handle Odd Number of Teams (Add a dummy for bye weeks)
    rotation_teams = list(teams)
    if len(rotation_teams) % 2 != 0:
        rotation_teams.append(None)
    
    num_teams = len(rotation_teams)
    total_rounds = num_teams - 1
    matches_per_round = num_teams // 2
    
    # 2. Calculate Date Distribution
    frequency_days = tournament.get_frequency_days()
    
    # If end_date is specified, calculate available match days
    if tournament.end_date:
        total_days = (tournament.end_date - tournament.start_date).days + 1
        # Calculate how many match days we can have
        max_match_days = (total_days + frequency_days - 1) // frequency_days
        
        # We need total_rounds * 2 match days (first leg + second leg)
        required_match_days = total_rounds * 2
        
        # Adjust frequency if needed to fit all matches
        if max_match_days < required_match_days:
            # Calculate minimum frequency needed
            frequency_days = max(1, total_days // required_match_days)
    
    fixtures = []
    current_match_date = tournament.start_date
    
    # --- PHASE 1: FIRST LEG ---
    first_leg_pairings = []  # Store pairings to mirror them in Phase 2
    
    for round_num in range(total_rounds):
        round_pairings = []
        for i in range(matches_per_round):
            home = rotation_teams[i]
            away = rotation_teams[num_teams - 1 - i]
            
            # If one is None, it's a bye week for the other team
            if home is not None and away is not None:
                match_time = get_randomized_match_time(tournament.default_match_time)
                
                # Alternate home/away on even rounds for better balance
                if round_num % 2 == 1:
                    home, away = away, home
                
                # Check if we're within the tournament date range
                if tournament.end_date and current_match_date > tournament.end_date:
                    # Skip this match if beyond end date
                    continue
                
                fixtures.append(
                    Match(
                        tournament=tournament,
                        home_team=home,
                        away_team=away,
                        match_date=current_match_date,
                        match_time=match_time,
                        status='scheduled'
                    )
                )
                round_pairings.append((home, away))
        
        first_leg_pairings.append(round_pairings)
        
        # Rotate teams: Keep index 0 fixed, rotate the rest clockwise
        rotation_teams.insert(1, rotation_teams.pop())
        
        # Increment date based on frequency setting
        current_match_date += timedelta(days=frequency_days)

    # --- PHASE 2: SECOND LEG ---
    # Add a small break between legs (optional, can be adjusted)
    if tournament.end_date:
        # Calculate remaining days for second leg
        remaining_days = (tournament.end_date - current_match_date).days
        if remaining_days > 0:
            # Add a proportional break (e.g., 10% of remaining time)
            break_days = max(1, min(5, remaining_days // 10))
            current_match_date += timedelta(days=break_days)
    else:
        current_match_date += timedelta(days=3)
    
    for round_pairings in first_leg_pairings:
        for home_orig, away_orig in round_pairings:
            # Check if we're within the tournament date range
            if tournament.end_date and current_match_date > tournament.end_date:
                # Stop scheduling if we've exceeded the end date
                break
            
            match_time = get_randomized_match_time(tournament.default_match_time)
            
            # Swap Home and Away from the first leg
            fixtures.append(
                Match(
                    tournament=tournament,
                    home_team=away_orig,
                    away_team=home_orig,
                    match_date=current_match_date,
                    match_time=match_time,
                    status='scheduled'
                )
            )
        
        # Increment date based on frequency setting
        current_match_date += timedelta(days=frequency_days)
        
        # Break if we've exceeded the end date
        if tournament.end_date and current_match_date > tournament.end_date:
            break
    
    Match.objects.bulk_create(fixtures)



def generate_knockout_fixtures(tournament, teams):
    teams_list = list(teams)
    random.shuffle(teams_list)
    
    match_date = tournament.start_date
    fixtures = []
    
    for i in range(0, len(teams_list) - 1, 2):
        if i + 1 < len(teams_list):
            match_time = get_randomized_match_time(tournament.default_match_time)
            
            fixtures.append(
                Match(
                    tournament=tournament,
                    home_team=teams_list[i],
                    away_team=teams_list[i + 1],
                    match_date=match_date,
                    match_time=match_time,
                    status='scheduled'
                )
            )
    
    Match.objects.bulk_create(fixtures)


def generate_group_stage_fixtures(tournament, teams):
    # Reuse the robust league logic for group stages
    generate_league_fixtures(tournament, teams)


def update_standings_after_match(match):
    if match.status != 'completed' or match.home_score is None or match.away_score is None:
        return
    
    # Use select_for_update to prevent race conditions during concurrent saves
    with transaction.atomic():
        home_standing = Standing.objects.select_for_update().get(tournament=match.tournament, team=match.home_team)
        away_standing = Standing.objects.select_for_update().get(tournament=match.tournament, team=match.away_team)
        
        home_standing.played += 1
        away_standing.played += 1
        
        home_standing.goals_for += match.home_score
        home_standing.goals_against += match.away_score
        away_standing.goals_for += match.away_score
        away_standing.goals_against += match.home_score
        
        if match.home_score > match.away_score:
            home_standing.won += 1
            home_standing.points += 3
            away_standing.lost += 1
            home_result = 'W'
            away_result = 'L'
        elif match.home_score < match.away_score:
            away_standing.won += 1
            away_standing.points += 3
            home_standing.lost += 1
            home_result = 'L'
            away_result = 'W'
        else:
            home_standing.drawn += 1
            away_standing.drawn += 1
            home_standing.points += 1
            away_standing.points += 1
            home_result = 'D'
            away_result = 'D'
        
        home_standing.form = (home_result + home_standing.form)[:5]
        away_standing.form = (away_result + away_standing.form)[:5]
        
        home_standing.save()
        away_standing.save()

