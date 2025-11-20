from django.db import models

class Highlight(models.Model):
    STATUS_CHOICES = [
        ('pending_verification', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    UPLOADED_BY_CHOICES = [
        ('home', 'Home Team'),
        ('away', 'Away Team'),
    ]
    
    match = models.ForeignKey('matches.Match', on_delete=models.CASCADE, related_name='highlights')
    uploaded_by_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='uploaded_highlights')
    uploaded_by_side = models.CharField(max_length=10, choices=UPLOADED_BY_CHOICES)
    
    video_file = models.FileField(upload_to='highlights/')
    thumbnail = models.ImageField(upload_to='highlight_thumbnails/', null=True, blank=True)
    
    duration = models.DurationField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending_verification')
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_highlights')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Highlight: {self.match} (uploaded by {self.uploaded_by_team.team_name})"
    
    class Meta:
        ordering = ['-uploaded_at']
