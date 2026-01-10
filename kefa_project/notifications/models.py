from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = [
        ('match.scheduled', 'Match Scheduled'),
        ('match.ready', 'Match Ready'),
        ('match.result', 'Match Result'),
        ('achievement', 'Achievement Unlocked'),
        ('tournament', 'Tournament Update'),
        ('payment', 'Payment Update'),
        ('system', 'System Message'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    link = models.CharField(max_length=255, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
