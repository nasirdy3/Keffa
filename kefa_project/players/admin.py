from django.contrib import admin
from .models import Player

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'efootball_id', 'device_type', 'created_at']
    search_fields = ['full_name', 'user__username', 'efootball_id', 'phone_number']
    list_filter = ['device_type', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
