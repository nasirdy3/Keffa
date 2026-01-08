from django.contrib import admin
from .models import Player, GovernanceLog

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'efootball_id', 'role', 'device_type', 'created_at']
    search_fields = ['full_name', 'user__username', 'efootball_id', 'phone_number']
    list_filter = ['role', 'device_type', 'created_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(GovernanceLog)
class GovernanceLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'admin', 'target_object', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['details', 'target_object', 'admin__username']

