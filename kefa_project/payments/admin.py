from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['registration', 'amount', 'payment_method', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['registration__team__team_name', 'transaction_reference']
    readonly_fields = ['created_at', 'updated_at']
