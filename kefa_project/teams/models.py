from django.db import models
from django.core.exceptions import ValidationError
import difflib

class Team(models.Model):
    player = models.OneToOneField('players.Player', on_delete=models.CASCADE, related_name='team')
    team_name = models.CharField(max_length=200, unique=True)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    squad_image = models.ImageField(upload_to='team_squads/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return str(self.team_name)
    
    def clean(self):
        """
        Validate team name to prevent 'similar' names that could confuse users.
        Uses difflib to check for >85% similarity.
        """
        if not self.team_name:
            return

        # Fetch all other team names (excluding self if editing)
        existing_names = Team.objects.exclude(pk=self.pk).values_list('team_name', flat=True)
        
        current_name_clean = self.team_name.lower().strip()
        
        for name in existing_names:
            name_clean = name.lower().strip()
            
            # 1. Direct contains check (e.g. "Kebbi FC" vs "Kebbi FC 2") - Optional, dependent on strictness
            # if current_name_clean == name_clean:
            #     raise ValidationError({'team_name': f"Team name '{self.team_name}' already exists."})

            # 2. Similarity Ratio Check
            matcher = difflib.SequenceMatcher(None, current_name_clean, name_clean)
            ratio = matcher.ratio()
            
            # Threshold: 0.85 (85% similar)
            if ratio > 0.85:
                raise ValidationError({
                    'team_name': f"Team name '{self.team_name}' is too similar to existing team '{name}'. Please choose a distinct name."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['team_name']

