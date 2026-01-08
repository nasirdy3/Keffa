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
    
    # Governance role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    
    full_name = models.CharField(max_length=200)
    efootball_id = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    
    # Updated phone_number: Relaxed constraint to allow migration on dirty data
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    
    device_type = models.CharField(max_length=20, choices=DEVICE_CHOICES)
    profile_picture = models.ImageField(upload_to='player_profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        # Safety check for role access in case it's not populated yet
        role_display = self.get_role_display() if hasattr(self, 'role') else 'User'
        return f"{self.full_name} (@{self.user.username}) - {role_display}"
    
    def clean(self):
        """
        Enforce unique email on related User model.
        """
        if self.user.email:
            if User.objects.filter(email=self.user.email).exclude(pk=self.user.pk).exists():
                raise ValidationError({'user': "This email address is already in use by another account."})

    def save(self, *args, **kwargs):
        self.full_clean()  # Trigger validation before saving
        super().save(*args, **kwargs)

    @property
    def get_whatsapp_link(self):
        """
        Sanitizes phone number and returns a wa.me link.
        """
        if not self.phone_number:
            return None
            
        clean_number = re.sub(r'\D', '', self.phone_number)
        if clean_number.startswith('0'):
            clean_number = '234' + clean_number[1:]
        return f"https://wa.me/{clean_number}"
    
    class Meta:
        ordering = ['-created_at']
        # CONSTRAINT REMOVED TEMPORARILY TO FIX MIGRATION DEADLOCK
        # We will re-add the UniqueConstraint after data cleanup.


# Audit Log for governance tracking
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
    target_object = models.CharField(max_length=200)  # e.g., "Match #123"
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin} - {self.action} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']

