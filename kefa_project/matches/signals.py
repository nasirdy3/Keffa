from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Q
from .models import Match
from kefa_project.tournaments.models import Standing

def recalculate_team_standing(tournament, team):
    """
    Recalculates stats for a specific team in a specific tournament
    based on all completed/verified matches.
    """
    # 1. Get or Create the Standing object to ensure it exists
    standing, created = Standing.objects.get_or_create(
        tournament=tournament,
        team=team
    )

    # 2. Fetch all 'finished' matches for this team in this tournament
    # We include completed matches and forfeit scenarios
    finished_matches = Match.objects.filter(
        tournament=tournament,
        status__in=['completed', 'home_forfeit', 'away_forfeit', 'both_forfeit']
    ).filter(
        Q(home_team=team) | Q(away_team=team)
    )

    # 3. Initialize counters
    played = 0
    won = 0
    drawn = 0
    lost = 0
    goals_for = 0
    goals_against = 0

    # 4. Iterate and Aggregate
    for match in finished_matches:
        played += 1
        
        # Determine if team was Home or Away
        is_home = (match.home_team == team)
        
        # Get scores (handle None values safely)
        home_score = match.home_score if match.home_score is not None else 0
        away_score = match.away_score if match.away_score is not None else 0
        
        if is_home:
            my_score = home_score
            opp_score = away_score
        else:
            my_score = away_score
            opp_score = home_score

        # Aggregate Goals
        goals_for += my_score
        goals_against += opp_score

        # Determine Result
        if match.status == 'both_forfeit':
            lost += 1 # Or drawn, depending on rules. Usually both get 0 points -> Loss/Draw
            # In your tasks.py, you set both scores to 0. Let's treat as loss or draw? 
            # Standard rule: 0 pts usually implies loss.
            # But 0-0 is technically a draw. 
            # KEFA Logic: If both forfeit, usually 0 points awarded. 
            # To achieve 0 points, we treat as Loss.
            pass 
        elif my_score > opp_score:
            won += 1
        elif my_score == opp_score:
            drawn += 1
        else:
            lost += 1

    # 5. Calculate Points
    # Win = 3, Draw = 1, Loss = 0
    points = (won * 3) + (drawn * 1)

    # 6. Update Form Guide (Last 5 matches)
    # This creates a string like "W W L D W"
    recent_matches = finished_matches.order_by('-match_date', '-match_time')[:5]
    form_list = []
    for match in recent_matches:
        is_home = (match.home_team == team)
        h_s = match.home_score if match.home_score is not None else 0
        a_s = match.away_score if match.away_score is not None else 0
        
        if match.status == 'both_forfeit':
            form_list.append('L')
        elif is_home:
            if h_s > a_s: form_list.append('W')
            elif h_s == a_s: form_list.append('D')
            else: form_list.append('L')
        else:
            if a_s > h_s: form_list.append('W')
            elif a_s == h_s: form_list.append('D')
            else: form_list.append('L')
    
    # Reverse to show oldest->newest or keep newest->oldest? 
    # Usually Form is displayed Left=Newest. 
    # Join and clean form (remove any unintentional spaces)
    form = "".join(form_list).replace(" ", "").upper()

    # 7. Save the Standing
    standing.played = played
    standing.won = won
    standing.drawn = drawn
    standing.lost = lost
    standing.goals_for = goals_for
    standing.goals_against = goals_against
    standing.points = points
    standing.form = form
    standing.save()


@receiver(post_save, sender=Match)
def update_standings_on_match_save(sender, instance, created, **kwargs):
    """
    Triggered whenever a Match is saved.
    Checks if the match is finished, then recalculates standings for both teams.
    """
    if instance.status in ['completed', 'home_forfeit', 'away_forfeit', 'both_forfeit']:
        # Recalculate for Home Team
        recalculate_team_standing(instance.tournament, instance.home_team)
        # Recalculate for Away Team
        recalculate_team_standing(instance.tournament, instance.away_team)


@receiver(post_delete, sender=Match)
def update_standings_on_match_delete(sender, instance, **kwargs):
    """
    Triggered if a Match is deleted (e.g. admin mistake).
    Recalculates to remove points/goals.
    """
    if instance.status in ['completed', 'home_forfeit', 'away_forfeit', 'both_forfeit']:
        recalculate_team_standing(instance.tournament, instance.home_team)
        recalculate_team_standing(instance.tournament, instance.away_team)
