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
    verified_registrations = tournament.registrations.filter(payment_verified=True).select_related('team')
    teams = [reg.team for reg in verified_registrations]
    
    if len(teams) < 2:
        return
    
    for team in teams:
        Standing.objects.get_or_create(
            tournament=tournament,
            team=team,
            defaults={
                'played': 0,
                'won': 0,
                'drawn': 0,
                'lost': 0,
                'goals_for': 0,
                'goals_against': 0,
                'points': 0,
                'form': '',
            }
        )
    
    if tournament.tournament_type in ['league', 'champions_league']:
        generate_league_fixtures(tournament, teams)
    elif tournament.tournament_type == 'knockout':
        generate_knockout_fixtures(tournament, teams)
    elif tournament.tournament_type == 'group_stage':
        generate_group_stage_fixtures(tournament, teams)


def generate_league_fixtures(tournament, teams):
    num_teams = len(teams)
    fixtures = []
    
    match_date = tournament.start_date
    
    for round_num in range(num_teams - 1):
        for i in range(num_teams // 2):
            home_team = teams[i]
            away_team = teams[num_teams - 1 - i]
            
            match_time = get_randomized_match_time(tournament.default_match_time)
            
            fixtures.append(
                Match(
                    tournament=tournament,
                    home_team=home_team,
                    away_team=away_team,
                    match_date=match_date,
                    match_time=match_time,
                    status='scheduled'
                )
            )
        
        teams.insert(1, teams.pop())
        match_date += timedelta(days=2)
    
    second_leg_date = match_date + timedelta(days=3)
    for match in list(fixtures):
        match_time = get_randomized_match_time(tournament.default_match_time)
        
        fixtures.append(
            Match(
                tournament=tournament,
                home_team=match.away_team,
                away_team=match.home_team,
                match_date=second_leg_date,
                match_time=match_time,
                status='scheduled'
            )
        )
        second_leg_date += timedelta(days=2)
    
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
    generate_league_fixtures(tournament, teams)


def update_standings_after_match(match):
    if match.status != 'completed' or match.home_score is None or match.away_score is None:
        return
    
    home_standing = Standing.objects.get(tournament=match.tournament, team=match.home_team)
    away_standing = Standing.objects.get(tournament=match.tournament, team=match.away_team)
    
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
