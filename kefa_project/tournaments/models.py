from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    
    MATCH_FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('every_2_days', 'Every 2 Days'),
        ('every_3_days', 'Every 3 Days'),
        ('weekly', 'Weekly'),
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
    
    # Automated Scheduling Fields
    match_frequency = models.CharField(max_length=20, choices=MATCH_FREQUENCY_CHOICES, default='every_2_days')
    matches_per_day = models.IntegerField(default=1, help_text='Maximum matches per day (for tournaments with multiple simultaneous matches)')
    auto_schedule_enabled = models.BooleanField(default=True, help_text='Enable automatic fixture scheduling')
    
    junior_league = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='senior_league')
    promotion_relegation_enabled = models.BooleanField(default=False)
    teams_to_promote = models.IntegerField(default=2)
    teams_to_relegate = models.IntegerField(default=2)
    
    fixtures_generated = models.BooleanField(default=False)
    
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
    
    def get_frequency_days(self):
        """Returns the number of days between matches based on frequency setting"""
        frequency_map = {
            'daily': 1,
            'every_2_days': 2,
            'every_3_days': 3,
            'weekly': 7,
        }
        return frequency_map.get(self.match_frequency, 2)
    
    def calculate_total_matches(self):
        """Calculate total matches needed for round-robin (league) format"""
        if self.tournament_type in ['league', 'champions_league']:
            n = self.current_teams_count
            # Double round-robin: n * (n-1) matches
            return n * (n - 1) if n > 1 else 0
        return 0
    
    def validate_scheduling_feasibility(self):
        """Check if the tournament date range can accommodate all matches"""
        if not self.end_date or not self.start_date:
            return True, "No end date specified"
        
        total_matches = self.calculate_total_matches()
        if total_matches == 0:
            return True, "No matches to schedule"
        
        from datetime import timedelta
        date_range = (self.end_date - self.start_date).days + 1
        frequency_days = self.get_frequency_days()
        
        # Calculate how many match days are available
        available_match_days = (date_range + frequency_days - 1) // frequency_days
        matches_per_round = self.current_teams_count // 2 if self.current_teams_count % 2 == 0 else (self.current_teams_count - 1) // 2
        
        # Total capacity considering matches_per_day
        total_capacity = available_match_days * self.matches_per_day * matches_per_round
        
        if total_capacity < total_matches:
            return False, f"Date range too short: need {total_matches} matches but can only fit {total_capacity}"
        
        return True, "Scheduling is feasible"
    
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

    def clean(self):
        """
        Enforce 'One League Only' Policy.
        A team cannot join a new 'league' if they are already in an active 'league'.
        """
        # Only enforce this restriction for League formats
        if self.tournament.tournament_type == 'league':
            # Check for other active league registrations for this team
            active_league_registrations = TournamentRegistration.objects.filter(
                team=self.team,
                tournament__tournament_type='league'
            ).exclude(
                tournament__status__in=['completed', 'cancelled']
            ).exclude(
                pk=self.pk # Exclude self if updating an existing registration
            )
            
            if active_league_registrations.exists():
                active_names = ", ".join([reg.tournament.name for reg in active_league_registrations])
                raise ValidationError(
                    f"Action Forbidden: {self.team.team_name} is already registered in an active league ({active_names}). "
                    "Teams can only participate in one League at a time."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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

