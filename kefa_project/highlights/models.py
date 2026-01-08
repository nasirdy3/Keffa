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
    
    # ARCHITECT UPDATE: Flexible Evidence System
    # Users can now upload a file, a screenshot, or a URL
    video_file = models.FileField(upload_to='highlights/videos/', null=True, blank=True)
    evidence_screenshot = models.ImageField(upload_to='highlights/screenshots/', null=True, blank=True)
    video_url = models.URLField(max_length=500, null=True, blank=True, help_text="External link to YouTube/Twitch")
    
    thumbnail = models.ImageField(upload_to='highlight_thumbnails/', null=True, blank=True)
    
    duration = models.DurationField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    description = models.TextField(blank=True)  # Added missing field referenced in views
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending_verification')
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_highlights')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Highlight: {self.match} (uploaded by {self.uploaded_by_team.team_name})"
    
    @property
    def evidence_type(self):
        if self.video_file:
            return 'video_file'
        if self.evidence_screenshot:
            return 'screenshot'
        if self.video_url:
            return 'video_url'
        return 'none'
    
    class Meta:
        ordering = ['-uploaded_at']

