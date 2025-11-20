from django.db import models

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
        ('offline', 'Offline/Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    registration = models.OneToOneField('tournaments.TournamentRegistration', on_delete=models.CASCADE, related_name='payment')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES)
    
    transaction_reference = models.CharField(max_length=200, unique=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for {self.registration.team.team_name} - {self.registration.tournament.name}"
    
    class Meta:
        ordering = ['-created_at']
