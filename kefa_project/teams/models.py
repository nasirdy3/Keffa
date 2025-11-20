from django.db import models

class Team(models.Model):
    player = models.OneToOneField('players.Player', on_delete=models.CASCADE, related_name='team')
    team_name = models.CharField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    squad_image = models.ImageField(upload_to='team_squads/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.team_name
    
    class Meta:
        ordering = ['team_name']
