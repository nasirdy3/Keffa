from django.db import models
from django.utils import timezone
from datetime import timedelta

class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ready_pending', 'Waiting for Ready Confirmation'),
        ('creating_game', 'Home Team Creating Game'),
        ('waiting_join', 'Waiting for Away Team to Join'),
        ('in_progress', 'In Progress'),
        ('awaiting_highlight', 'Awaiting Highlights'),
        ('pending_verification', 'Pending Verification'),
        ('completed', 'Completed'),
        ('home_forfeit', 'Home Team Forfeit'),
        ('away_forfeit', 'Away Team Forfeit'),
        ('both_forfeit', 'Both Teams Forfeit'),
        ('postponed', 'Postponed'),
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
    
    game_code = models.CharField(max_length=50, blank=True)
    game_code_created_at = models.DateTimeField(null=True, blank=True)
    
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_matches')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.home_team.team_name} vs {self.away_team.team_name} - {self.match_date}"
    
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
