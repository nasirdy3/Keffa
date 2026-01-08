from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class Player(models.Model):
    DEVICE_CHOICES = [
        ('android', 'Android'),
        ('iphone', 'iPhone'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    ]
    
    # Governance Roles
    ROLE_CHOICES = [
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    # ARCHITECT NOTE: New role field for governance. Default is 'user'.
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    
    full_name = models.CharField(max_length=200)
    efootball_id = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    # ARCHITECT NOTE: Added unique=True to enforce DB level uniqueness
    phone_number = models.CharField(max_length=20, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES)
    profile_picture = models.ImageField(upload_to='player_profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.full_name} (@{self.user.username}) - {self.get_role_display()}"
    
    def clean(self):
        """
        Strictly enforce Email uniqueness on the related User model.
        Django's default User model allows duplicate emails; we forbid it here.
        """
        if self.user.email:
            # Check if any OTHER user has this email
            if User.objects.filter(email=self.user.email).exclude(pk=self.user.pk).exists():
                raise ValidationError({'user': "This email address is already in use by another account."})

    def save(self, *args, **kwargs):
        self.full_clean() # Trigger validation before saving
        super().save(*args, **kwargs)

    @property
    def get_whatsapp_link(self):
        """
        Sanitizes phone number and returns a wa.me link.
        Assumes Nigerian numbers (234) if no country code provided.
        """
        if not self.phone_number:
            return None
            
        # Remove all non-numeric characters
        clean_number = re.sub(r'\D', '', self.phone_number)
        
        # Basic check: If it starts with '0' (e.g. 080...), replace with '234'
        if clean_number.startswith('0'):
            clean_number = '234' + clean_number[1:]
            
        return f"https://wa.me/{clean_number}"
    
    class Meta:
        ordering = ['-created_at']

# ARCHITECT NOTE: New Audit Log model for strict governance tracking
class GovernanceLog(models.Model):
    ACTION_CHOICES = [
        ('role_change', 'Role Changed'),
        ('payment_verify', 'Payment Verified'),
        ('match_verify', 'Match Verified'),
        ('highlight_verify', 'Highlight Verified'),
        ('manual_override', 'Manual Override'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='governance_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_object = models.CharField(max_length=200) # E.g., "Match #123" or "User @john"
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin} - {self.action} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']

