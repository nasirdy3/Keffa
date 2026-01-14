import random
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction
from .models import Tournament, TournamentRegistration, Standing
from kefa_project.matches.models import Match
from kefa_project.achievements.models import Badge, PlayerBadge, Trophy
from django.db import models


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


def check_team_availability(team, date, exclude_match=None, tournament_priority=None):
    """
    Check if a team is available on a specific date.
    Returns (is_available: bool, blocking_match: Match|None)
    
    Args:
        team: Team object to check
        date: Date to check availability for
        exclude_match: Match to exclude from check (when rescheduling)
        tournament_priority: Priority of tournament being scheduled (for priority-based blocking)
    """
    # Query all matches for this team on the given date
    matches_on_date = Match.objects.filter(
        match_date=date
    ).filter(
        models.Q(home_team=team) | models.Q(away_team=team)
    ).select_related('tournament')
    
    # Exclude specific match if provided
    if exclude_match:
        matches_on_date = matches_on_date.exclude(pk=exclude_match.pk)
    
    # If tournament_priority is provided, only block if existing match has higher priority
    if tournament_priority is not None:
        matches_on_date = matches_on_date.filter(
            tournament__priority__lt=tournament_priority
        )
    
    blocking_match = matches_on_date.first()
    is_available = blocking_match is None
    
    return is_available, blocking_match


def get_valid_weekday_dates(start_date, end_date, allowed_weekdays, frequency_days=1):
    """
    Generate list of valid dates within range that match allowed weekdays.
    
    Args:
        start_date: Starting date
        end_date: Ending date
        allowed_weekdays: List of allowed weekday numbers (0=Monday, 6=Sunday)
        frequency_days: Minimum days between matches
    
    Returns:
        List of valid dates sorted chronologically
    """
    if not allowed_weekdays:
        # If no weekday restrictions, return all dates with frequency
        valid_dates = []
        current = start_date
        while current <= end_date:
            valid_dates.append(current)
            current += timedelta(days=frequency_days)
        return valid_dates
    
    valid_dates = []
    current = start_date
    last_added = None
    
    while current <= end_date:
        # Check if current date's weekday is in allowed list
        if current.weekday() in allowed_weekdays:
            # Check frequency constraint
            if last_added is None or (current - last_added).days >= frequency_days:
                valid_dates.append(current)
                last_added = current
        current += timedelta(days=1)
    
    return valid_dates


def find_next_available_date(team1, team2, start_date, allowed_weekdays, tournament_priority, end_date=None, max_days_ahead=365):
    """
    Find the next date where both teams are available.
    
    Args:
        team1: First team
        team2: Second team
        start_date: Date to start searching from
        allowed_weekdays: List of allowed weekday numbers
        tournament_priority: Priority of tournament being scheduled
        end_date: Optional end date constraint
        max_days_ahead: Maximum days to search ahead
    
    Returns:
        Next valid date or None if no date available
    """
    
    search_end = end_date if end_date else start_date + timedelta(days=max_days_ahead)
    current = start_date
    
    while current <= search_end:
        # Check if weekday is allowed
        if not allowed_weekdays or current.weekday() in allowed_weekdays:
            # Check both teams' availability
            team1_available, _ = check_team_availability(team1, current, tournament_priority=tournament_priority)
            team2_available, _ = check_team_availability(team2, current, tournament_priority=tournament_priority)
            
            if team1_available and team2_available:
                return current
        
        current += timedelta(days=1)
    
    return None


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
    Implements Round-Robin Algorithm with Intelligent Date Distribution.
    Supports both Single and Double Round Robin based on tournament.round_robin_type.
    Key Features:
    1. Respects weekday rules (league: Thu-Sun, cup: Mon-Wed)
    2. Checks team availability across all competitions
    3. Respects priority-based scheduling (higher priority blocks lower priority)
    4. Distributes matches evenly across the entire tournament date range
    5. Handles odd number of teams with bye weeks
    6. Maintains proper home/away balance
    """
    
    # 1. Handle Odd Number of Teams (Add a dummy for bye weeks)
    rotation_teams = list(teams)
    if len(rotation_teams) % 2 != 0:
        rotation_teams.append(None)
    
    num_teams = len(rotation_teams)
    total_rounds = num_teams - 1
    matches_per_round = num_teams // 2
    
    # 2. Get scheduling constraints
    frequency_days = tournament.get_frequency_days()
    allowed_weekdays = tournament.get_allowed_weekdays()
    tournament_priority = tournament.priority
    
    # 3. Get valid dates based on weekday rules
    if tournament.end_date:
        valid_dates = get_valid_weekday_dates(
            tournament.start_date,
            tournament.end_date,
            allowed_weekdays,
            frequency_days
        )
    else:
        # If no end date, generate dates for reasonable period
        estimated_end = tournament.start_date + timedelta(days=total_rounds * frequency_days * 3)
        valid_dates = get_valid_weekday_dates(
            tournament.start_date,
            estimated_end,
            allowed_weekdays,
            frequency_days
        )
    
    if not valid_dates:
        # Fallback: use start_date if no valid dates found
        valid_dates = [tournament.start_date]
    
    fixtures = []
    date_index = 0
    
    # --- PHASE 1: FIRST LEG (or ONLY leg for single round robin) ---
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
                
                # Find next available date for both teams
                if date_index < len(valid_dates):
                    current_match_date = valid_dates[date_index]
                else:
                    # Extend beyond valid_dates if needed
                    last_date = valid_dates[-1] if valid_dates else tournament.start_date
                    current_match_date = last_date + timedelta(days=frequency_days)
                
                # Check team availability and find next valid date if needed
                max_attempts = 30  # Prevent infinite loops
                attempts = 0
                while attempts < max_attempts:
                    team1_avail, _ = check_team_availability(home, current_match_date, tournament_priority=tournament_priority)
                    team2_avail, _ = check_team_availability(away, current_match_date, tournament_priority=tournament_priority)
                    
                    if team1_avail and team2_avail:
                        break
                    
                    # Find next valid date
                    next_date = find_next_available_date(
                        home, away, 
                        current_match_date + timedelta(days=1),
                        allowed_weekdays,
                        tournament_priority,
                        tournament.end_date
                    )
                    
                    if next_date:
                        current_match_date = next_date
                    else:
                        # No valid date found, use current anyway (admin will need to resolve)
                        break
                    
                    attempts += 1
                
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
        
        # Move to next date slot
        date_index += 1

    # --- PHASE 2: SECOND LEG (only for double round robin) ---
    if tournament.round_robin_type == 'double':
        # Add a small break between legs
        if date_index < len(valid_dates):
            date_index += 1  # Skip one date slot for break
        
        for round_pairings in first_leg_pairings:
            for home_orig, away_orig in round_pairings:
                # Get next available date
                if date_index < len(valid_dates):
                    current_match_date = valid_dates[date_index]
                else:
                    last_date = valid_dates[-1] if valid_dates else tournament.start_date
                    current_match_date = last_date + timedelta(days=frequency_days * (date_index - len(valid_dates) + 1))
                
                # Check team availability
                max_attempts = 30
                attempts = 0
                while attempts < max_attempts:
                    team1_avail, _ = check_team_availability(away_orig, current_match_date, tournament_priority=tournament_priority)
                    team2_avail, _ = check_team_availability(home_orig, current_match_date, tournament_priority=tournament_priority)
                    
                    if team1_avail and team2_avail:
                        break
                    
                    next_date = find_next_available_date(
                        away_orig, home_orig,
                        current_match_date + timedelta(days=1),
                        allowed_weekdays,
                        tournament_priority,
                        tournament.end_date
                    )
                    
                    if next_date:
                        current_match_date = next_date
                    else:
                        break
                    
                    attempts += 1
                
                # Check if we're within the tournament date range
                if tournament.end_date and current_match_date > tournament.end_date:
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
            
            date_index += 1
            
            if tournament.end_date and date_index < len(valid_dates) and valid_dates[date_index] > tournament.end_date:
                break
    
    Match.objects.bulk_create(fixtures)


def generate_knockout_fixtures(tournament, teams):
    """
    Generate knockout bracket with proper round structure and match linking.
    Supports single-elimination brackets with automatic winner progression.
    
    Features:
    - Handles power-of-2 team counts (4, 8, 16, 32)
    - Creates proper bracket structure with feeder matches
    - Links matches for automatic winner advancement
    - Respects weekday rules and team availability
    - Assigns knockout_round labels (Quarter-finals, Semi-finals, Final)
    """
    import math
    
    teams_list = list(teams)
    num_teams = len(teams_list)
    
    if num_teams < 2:
        return
    
    # Shuffle teams for random bracket seeding
    random.shuffle(teams_list)
    
    # Calculate number of rounds needed
    # Round up to next power of 2
    bracket_size = 2 ** math.ceil(math.log2(num_teams))
    num_rounds = int(math.log2(bracket_size))
    
    # Get scheduling constraints
    allowed_weekdays = tournament.get_allowed_weekdays()
    tournament_priority = tournament.priority
    frequency_days = tournament.get_frequency_days()
    
    # Determine round names based on bracket size
    round_names = []
    if num_rounds >= 5:
        round_names = ['round_of_32', 'round_of_16', 'quarter_final', 'semi_final', 'final']
    elif num_rounds == 4:
        round_names = ['round_of_16', 'quarter_final', 'semi_final', 'final']
    elif num_rounds == 3:
        round_names = ['quarter_final', 'semi_final', 'final']
    elif num_rounds == 2:
        round_names = ['semi_final', 'final']
    else:
        round_names = ['final']
    
    # Pad teams with None for byes if not power of 2
    while len(teams_list) < bracket_size:
        teams_list.append(None)
    
    # Build bracket from bottom up
    # Store matches by round: rounds[0] = first round, rounds[-1] = final
    rounds = [[] for _ in range(num_rounds)]
    
    # Generate first round matches
    current_date = tournament.start_date
    
    for i in range(0, bracket_size, 2):
        team1 = teams_list[i]
        team2 = teams_list[i + 1]
        
        # Skip if both teams are None (shouldn't happen but safety check)
        if team1 is None and team2 is None:
            continue
        
        # Handle byes: if one team is None, the other advances automatically
        if team1 is None or team2 is None:
            # Create a bye match (will be marked as completed with winner)
            actual_team = team1 if team1 else team2
            match = Match(
                tournament=tournament,
                home_team=actual_team,
                away_team=actual_team,  # Placeholder
                match_date=current_date,
                match_time=tournament.default_match_time,
                status='completed',  # Bye matches are auto-completed
                home_score=3,
                away_score=0,
                knockout_round=round_names[0] if round_names else 'round_1'
            )
        else:
            # Find valid date respecting weekday rules and availability
            valid_date = find_next_available_date(
                team1, team2,
                current_date,
                allowed_weekdays,
                tournament_priority,
                tournament.end_date
            )
            
            if not valid_date:
                valid_date = current_date
            
            match_time = get_randomized_match_time(tournament.default_match_time)
            
            match = Match(
                tournament=tournament,
                home_team=team1,
                away_team=team2,
                match_date=valid_date,
                match_time=match_time,
                status='scheduled',
                knockout_round=round_names[0] if round_names else 'round_1'
            )
        
        rounds[0].append(match)
    
    # Generate subsequent rounds and link matches
    for round_idx in range(1, num_rounds):
        matches_in_round = len(rounds[round_idx - 1]) // 2
        
        # Move date forward for next round
        current_date += timedelta(days=frequency_days * 2)
        
        for match_idx in range(matches_in_round):
            # Find valid date
            if allowed_weekdays:
                while current_date.weekday() not in allowed_weekdays:
                    current_date += timedelta(days=1)
            
            match_time = get_randomized_match_time(tournament.default_match_time)
            
            # Create match with TBD teams (will be filled by winners)
            match = Match(
                tournament=tournament,
                home_team=teams_list[0],  # Placeholder - will be updated by winner
                away_team=teams_list[0],  # Placeholder - will be updated by winner
                match_date=current_date,
                match_time=match_time,
                status='scheduled',
                knockout_round=round_names[round_idx] if round_idx < len(round_names) else f'round_{round_idx + 1}'
            )
            
            rounds[round_idx].append(match)
    
    # Save all matches first (need PKs for foreign key relationships)
    all_matches = []
    for round_matches in rounds:
        all_matches.extend(round_matches)
    
    Match.objects.bulk_create(all_matches)
    
    # Now link matches together (feeder_match_1/2 and next_match)
    # Refresh from DB to get PKs
    all_matches = Match.objects.filter(
        tournament=tournament,
        knockout_round__isnull=False
    ).order_by('match_date', 'id')
    
    # Rebuild rounds list with saved matches
    rounds = [[] for _ in range(num_rounds)]
    for match in all_matches:
        if match.knockout_round == (round_names[0] if round_names else 'round_1'):
            rounds[0].append(match)
        elif num_rounds > 1 and match.knockout_round == (round_names[1] if len(round_names) > 1 else 'round_2'):
            rounds[1].append(match)
        elif num_rounds > 2 and match.knockout_round == (round_names[2] if len(round_names) > 2 else 'round_3'):
            rounds[2].append(match)
        elif num_rounds > 3 and match.knockout_round == (round_names[3] if len(round_names) > 3 else 'round_4'):
            rounds[3].append(match)
        elif num_rounds > 4 and match.knockout_round == (round_names[4] if len(round_names) > 4 else 'round_5'):
            rounds[4].append(match)
    
    # Link matches
    for round_idx in range(num_rounds - 1):
        for match_idx, match in enumerate(rounds[round_idx]):
            # This match feeds into the next round
            next_round_match_idx = match_idx // 2
            if next_round_match_idx < len(rounds[round_idx + 1]):
                next_match = rounds[round_idx + 1][next_round_match_idx]
                match.next_match = next_match
                
                # Set as feeder match
                if match_idx % 2 == 0:
                    next_match.feeder_match_1 = match
                else:
                    next_match.feeder_match_2 = match
                
                match.save()
                next_match.save()


def generate_group_stage_fixtures(tournament, teams):
    # Reuse the robust league logic for group stages
    generate_league_fixtures(tournament, teams)


def get_bracket_structure(tournament):
    """
    Build hierarchical bracket structure for frontend visualization.
    Returns JSON-serializable dict with rounds, matches, and connections.
    """
    # Get all knockout matches for this tournament
    knockout_matches = Match.objects.filter(
        tournament=tournament,
        knockout_round__isnull=False
    ).select_related('home_team', 'away_team', 'next_match').order_by('match_date', 'id')
    
    if not knockout_matches.exists():
        return {'rounds': [], 'total_rounds': 0}
    
    # Group matches by round
    rounds_dict = {}
    for match in knockout_matches:
        round_name = match.knockout_round
        if round_name not in rounds_dict:
            rounds_dict[round_name] = []
        
        # Build match data
        winner = match.get_winner()
        match_data = {
            'id': match.id,
            'home_team': {
                'id': match.home_team.id,
                'name': match.home_team.team_name,
                'is_winner': winner == match.home_team if winner else False
            },
            'away_team': {
                'id': match.away_team.id,
                'name': match.away_team.team_name,
                'is_winner': winner == match.away_team if winner else False
            },
            'home_score': match.home_score,
            'away_score': match.away_score,
            'aggregate_home': match.aggregate_home_score,
            'aggregate_away': match.aggregate_away_score,
            'status': match.status,
            'match_date': match.match_date.isoformat(),
            'match_time': match.match_time.strftime('%H:%M'),
            'next_match_id': match.next_match.id if match.next_match else None,
            'round': round_name
        }
        rounds_dict[round_name].append(match_data)
    
    # Order rounds from earliest to latest
    round_order = ['round_of_32', 'round_of_16', 'quarter_final', 'semi_final', 'final']
    ordered_rounds = []
    
    for round_name in round_order:
        if round_name in rounds_dict:
            ordered_rounds.append({
                'name': round_name,
                'display_name': dict(Match.KNOCKOUT_ROUND_CHOICES).get(round_name, round_name),
                'matches': rounds_dict[round_name]
            })
    
    return {
        'rounds': ordered_rounds,
        'total_rounds': len(ordered_rounds),
        'tournament': {
            'id': tournament.id,
            'name': tournament.name
        }
    }



def update_standings_after_match(match):
    if match.status != 'completed' or match.home_score is None or match.away_score is None:
        return
    
    # Handle knockout matches - advance winner to next round
    if match.knockout_round:
        match.advance_winner()
        # Knockout matches don't update standings, just advance winners
        return
    
    # Handle league/group stage matches - update standings
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
        
        # Check Milestones for both teams
        from kefa_project.achievements.services import check_match_milestones
        check_match_milestones(match.home_team)
        check_match_milestones(match.away_team)



def process_season_end(tournament):
    """
    Finalizes a tournament season.
    1. Locks tournament as completed.
    2. Awards Trophies (Gold, Silver, Bronze).
    3. Awards Badges (Winner, Runner-Up, Top Scorer, Best Defence).
    4. Qualifies Top 4 for Champions League (if applicable).
    """
    if tournament.status == 'completed':
        return False, "Tournament already completed"

    with transaction.atomic():
        # 1. Get Final Standings
        # Order by points DESC, then GD DESC, then Goals For DESC
        standings = Standing.objects.filter(tournament=tournament).order_by(
            '-points', '-goal_difference', '-goals_for'
        )
        
        if not standings.exists():
            return False, "No standings found"

        # 2. Award Trophies & Positional Badges
        winner = standings[0]
        runner_up = standings[1] if len(standings) > 1 else None
        third_place = standings[2] if len(standings) > 2 else None
        
        # Gold Trophy + Winner Badge
        Trophy.objects.create(team=winner.team, tournament=tournament, trophy_type='gold', position=1)
        _award_badge(winner.team.player, 'tournament_winner', tournament)
        
        # Silver Trophy + Runner Up Badge
        if runner_up:
            Trophy.objects.create(team=runner_up.team, tournament=tournament, trophy_type='silver', position=2)
            _award_badge(runner_up.team.player, 'runner_up', tournament)
            
        # Bronze Trophy
        if third_place:
            Trophy.objects.create(team=third_place.team, tournament=tournament, trophy_type='bronze', position=3)

        # 3. Award Stat Badges
        # Best Attack (Top Scorer Team)
        # Re-query to find top scorer
        best_attack = standings.order_by('-goals_for', '-points').first()
        if best_attack and best_attack.goals_for > 0:
            _award_badge(best_attack.team.player, 'top_scorer', tournament)
            
        # Best Defence
        best_defence = standings.order_by('goals_against', '-points').first()
        if best_defence:
            _award_badge(best_defence.team.player, 'best_defence', tournament)

        # 4. Access Champions League Qualification (League Only)
        if tournament.tournament_type == 'league':
            _process_champion_league_qualification(tournament, standings)
            _handle_promotion_relegation(tournament, standings)

        # 5. Mark Completed
        tournament.status = 'completed'
        tournament.save()
        
    return True, f"Season finalized. Winner: {winner.team.team_name}"


def _award_badge(player, badge_type, tournament):
    """Helper to award a badge if it exists in the system."""
    try:
        badge_def = Badge.objects.get(badge_type=badge_type)
        PlayerBadge.objects.get_or_create(
            player=player,
            badge=badge_def,
            tournament=tournament,
            defaults={'notes': f"Awarded for {badge_def.name} in {tournament.name}"}
        )
    except Badge.DoesNotExist:
        pass # Badge type not defined in system, skip


def _process_champion_league_qualification(source_tournament, standings):
    """
    Qualifies top teams for the Champions League.
    Typically top 4 teams from the league qualify.
    """
    # Find an upcoming Champions League
    # We look for one that is in registration phase
    cl_tournament = Tournament.objects.filter(
        tournament_type='champions_league',
        status__in=['registration', 'locked']
    ).order_by('start_date').first()
    
    if not cl_tournament:
        return

    # Determine how many qualify. Default to 4.
    # In a real scenario, this might be dynamic or configured on the tournament.
    qualifiers_count = 4
    qualifying_standings = standings[:qualifiers_count]
    
    for standing in qualifying_standings:
        team = standing.team
        
        # Avoid duplicate registration
        if not TournamentRegistration.objects.filter(tournament=cl_tournament, team=team).exists():
            # Check if team limit reached
            if cl_tournament.is_full:
                break
                
            TournamentRegistration.objects.create(
                tournament=cl_tournament,
                team=team,
                payment_verified=True # Auto-verify logic
            )

def _handle_promotion_relegation(tournament, standings):
    """
    Identifies teams for promotion and relegation.
    Since 'Next Season' creation is manual, this function:
    1. Creates system notifications for the affected teams.
    2. Tags the Standing model (requires migration) OR just returns the info.
    For this implementation, we will use System Notifications to inform Admins and Teams.
    """
    from kefa_project.notifications.services import create_notification
    
    if not tournament.promotion_relegation_enabled:
        return

    # RELEGATION (From this league down)
    relegation_count = tournament.teams_to_relegate
    relegated_standings = standings.reverse()[:relegation_count] # Bottom N
    
    for standing in relegated_standings:
        # Notify Team Captain
        create_notification(
            recipient=standing.team.player.user,
            title="Relegation Warning",
            message=f"Your team finished in the relegation zone (Position {len(standings) - list(standings).index(standing)}). You may be relegated to the lower division next season.",
            notification_type="tournament"
        )
        # TODO: Mark 'relegated' boolean on Standing if field existed
        
    # PROMOTION (From Junior League up)
    # This logic usually runs when the JUNIOR league ends, but we can check here if connected
    if tournament.junior_league and tournament.junior_league.status == 'completed':
        junior_standings = Standing.objects.filter(tournament=tournament.junior_league).order_by('-points', '-goal_difference')
        promote_count = tournament.teams_to_promote
        promoted_standings = junior_standings[:promote_count]
        
        for standing in promoted_standings:
             create_notification(
                recipient=standing.team.player.user,
                title="Promotion!",
                message=f"Congratulations! Your team finished in the promotion zone of {tournament.junior_league.name}. You are eligible for promotion to {tournament.name} next season.",
                notification_type="achievement"
            )
