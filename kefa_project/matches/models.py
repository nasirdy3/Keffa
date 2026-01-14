from django.db import models
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField


class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ready_pending', 'Waiting for Ready Confirmation'),
        ('in_progress', 'In Progress'),
        ('awaiting_highlight', 'Awaiting Highlights'),
        ('pending_verification', 'Pending Verification'),
        ('completed', 'Completed'),
        ('home_forfeit', 'Home Team Forfeit'),
        ('away_forfeit', 'Away Team Forfeit'),
        ('both_forfeit', 'Both Teams Forfeit'),
        ('postponed', 'Postponed'),
    ]
    
    KNOCKOUT_ROUND_CHOICES = [
        ('round_of_32', 'Round of 32'),
        ('round_of_16', 'Round of 16'),
        ('quarter_final', 'Quarter-finals'),
        ('semi_final', 'Semi-finals'),
        ('final', 'Final'),
    ]
    
    tournament = models.ForeignKey('tournaments.Tournament', on_delete=models.CASCADE, related_name='matches')
    home_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='away_matches')
    
    match_date = models.DateField()
    match_time = models.TimeField()
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='scheduled')
    
    home_ready = models.BooleanField(default=False)
    away_ready = models.BooleanField(default=False)
    ready_time_start = models.DateTimeField(null=True, blank=True)
    
    # Legacy fields kept for FriendlyMatch compatibility and DB stability
    game_code = models.CharField(max_length=50, blank=True)
    game_code_created_at = models.DateTimeField(null=True, blank=True)
    
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_matches')
    
    # Knockout Bracket Fields
    knockout_round = models.CharField(
        max_length=20, 
        choices=KNOCKOUT_ROUND_CHOICES, 
        null=True, 
        blank=True,
        help_text='Knockout stage round (e.g., Quarter-finals, Semi-finals)'
    )
    next_match = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='previous_matches',
        help_text='The match that the winner of this match advances to'
    )
    feeder_match_1 = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='feeds_to_1',
        help_text='First match that feeds into this match'
    )
    feeder_match_2 = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='feeds_to_2',
        help_text='Second match that feeds into this match'
    )
    aggregate_home_score = models.IntegerField(
        null=True, 
        blank=True,
        help_text='Aggregate score for two-leg knockout ties'
    )
    aggregate_away_score = models.IntegerField(
        null=True, 
        blank=True,
        help_text='Aggregate score for two-leg knockout ties'
    )

    # Match Summary Fields
    match_summary = models.TextField(blank=True, help_text="Written summary of the match")
    summary_image = CloudinaryField('image', blank=True, null=True, help_text="Image attachment for match summary")
    summary_video = CloudinaryField('video', resource_type='video', blank=True, null=True, help_text="Video attachment for match summary")

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.home_team.team_name} vs {self.away_team.team_name} - {self.match_date}"
    
    def get_winner(self):
        """Determine the winner of this match (for knockout progression)"""
        if self.status not in ['completed', 'home_forfeit', 'away_forfeit']:
            return None
        
        # Handle forfeits
        if self.status == 'home_forfeit':
            return self.away_team
        if self.status == 'away_forfeit':
            return self.home_team
        
        # For two-leg knockouts, use aggregate score
        if self.aggregate_home_score is not None and self.aggregate_away_score is not None:
            if self.aggregate_home_score > self.aggregate_away_score:
                return self.home_team
            elif self.aggregate_away_score > self.aggregate_home_score:
                return self.away_team
            else:
                return None  # Draw - would need penalty shootout or away goals rule
        
        # For single-leg matches
        if self.home_score is not None and self.away_score is not None:
            if self.home_score > self.away_score:
                return self.home_team
            elif self.away_score > self.home_score:
                return self.away_team
            else:
                return None  # Draw - would need extra time/penalties
        
        return None
    
    def advance_winner(self):
        """Advance the winner to the next round (if applicable)"""
        if not self.next_match or not self.knockout_round:
            return False
        
        winner = self.get_winner()
        if not winner:
            return False
        
        # Determine which slot in the next match to fill
        # If this match is feeder_match_1, winner goes to home_team
        # If this match is feeder_match_2, winner goes to away_team
        if self.next_match.feeder_match_1 == self:
            self.next_match.home_team = winner
            self.next_match.save()
            return True
        elif self.next_match.feeder_match_2 == self:
            self.next_match.away_team = winner
            self.next_match.save()
            return True
        
        return False
    
    
    class Meta:
        ordering = ['match_date', 'match_time']
        verbose_name_plural = 'Matches'


class MatchPostponement(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('accepted_by_opponent', 'Accepted by Opponent'),
        ('pending_admin', 'Pending Admin Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='postponement_requests')
    requested_by = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='postponement_requests')
    opponent_accepted = models.BooleanField(default=False)
    
    reason = models.TextField()
    proposed_date = models.DateField()
    proposed_time = models.TimeField()
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='requested')
    admin_response = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Postponement Request for {self.match}"


class FriendlyMatch(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open for Acceptance'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    created_by_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='created_friendlies')
    opponent_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, null=True, blank=True, related_name='accepted_friendlies')
    
    game_code = models.CharField(max_length=50)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Friendly Match by {self.created_by_team.team_name}"
    
    class Meta:
        ordering = ['-created_at']

