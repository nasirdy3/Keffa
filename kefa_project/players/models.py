from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    DEVICE_CHOICES = [
        ('android', 'Android'),
        ('iphone', 'iPhone'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    full_name = models.CharField(max_length=200)
    efootball_id = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES)
    profile_picture = models.ImageField(upload_to='player_profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} (@{self.user.username})"
    
    class Meta:
        ordering = ['-created_at']
