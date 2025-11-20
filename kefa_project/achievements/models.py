from django.db import models

class Badge(models.Model):
    BADGE_TYPES = [
        ('tournament_winner', 'Tournament Winner'),
        ('runner_up', 'Runner-Up'),
        ('top_scorer', 'Top Scorer'),
        ('best_defence', 'Best Defence'),
        ('unbeaten_streak', '10-Match Unbeaten'),
        ('fastest_goal', 'Fastest Goal'),
        ('player_of_week', 'Player of the Week'),
        ('custom', 'Custom Badge'),
    ]
    
    name = models.CharField(max_length=100)
    badge_type = models.CharField(max_length=25, choices=BADGE_TYPES)
    description = models.TextField()
    icon = models.ImageField(upload_to='badges/', null=True, blank=True)
    
    is_automatic = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_badge_type_display()})"
    
    class Meta:
        ordering = ['name']


class PlayerBadge(models.Model):
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
    tournament = models.ForeignKey('tournaments.Tournament', on_delete=models.CASCADE, null=True, blank=True, related_name='badges_awarded')
    
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='badges_awarded')
    
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.badge.name} awarded to {self.player.full_name}"
    
    class Meta:
        ordering = ['-awarded_at']


class Trophy(models.Model):
    TROPHY_TYPES = [
        ('gold', 'Gold Trophy'),
        ('silver', 'Silver Trophy'),
        ('bronze', 'Bronze Trophy'),
    ]
    
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='trophies')
    tournament = models.ForeignKey('tournaments.Tournament', on_delete=models.CASCADE, related_name='trophies')
    trophy_type = models.CharField(max_length=10, choices=TROPHY_TYPES)
    
    position = models.IntegerField()
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_trophy_type_display()} - {self.team.team_name} ({self.tournament.name})"
    
    class Meta:
        ordering = ['-awarded_at']
        verbose_name_plural = 'Trophies'
