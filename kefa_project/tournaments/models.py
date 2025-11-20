from django.db import models
from django.utils import timezone

class Tournament(models.Model):
    TOURNAMENT_TYPES = [
        ('league', 'League Format'),
        ('knockout', 'Knockout Format'),
        ('group_stage', 'Group Stage Format'),
        ('mixed', 'Mixed Format'),
        ('champions_league', 'eFootball Champions League'),
    ]
    
    STATUS_CHOICES = [
        ('registration', 'Registration Open'),
        ('locked', 'Registration Locked'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES)
    team_limit = models.IntegerField()
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prize = models.TextField(blank=True)
    rules = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registration')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    default_match_time = models.TimeField(default='17:00:00')
    
    junior_league = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='senior_league')
    promotion_relegation_enabled = models.BooleanField(default=False)
    teams_to_promote = models.IntegerField(default=2)
    teams_to_relegate = models.IntegerField(default=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_tournament_type_display()})"
    
    @property
    def current_teams_count(self):
        return self.registrations.filter(payment_verified=True).count()
    
    @property
    def is_full(self):
        return self.current_teams_count >= self.team_limit
    
    class Meta:
        ordering = ['-created_at']


class TournamentRegistration(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='registrations')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='tournament_registrations')
    payment_verified = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['tournament', 'team']
        ordering = ['registered_at']
    
    def __str__(self):
        return f"{self.team.team_name} - {self.tournament.name}"


class Standing(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='standings')
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='standings')
    
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    drawn = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    
    form = models.CharField(max_length=10, blank=True)
    
    class Meta:
        unique_together = ['tournament', 'team']
        ordering = ['-points', '-goals_for', 'goals_against']
    
    def __str__(self):
        return f"{self.team.team_name} - {self.tournament.name}"
    
    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against
