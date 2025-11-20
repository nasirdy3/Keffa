from django.contrib import admin
from .models import Badge, PlayerBadge, Trophy

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'is_automatic', 'created_at']
    list_filter = ['badge_type', 'is_automatic']
    search_fields = ['name', 'description']

@admin.register(PlayerBadge)
class PlayerBadgeAdmin(admin.ModelAdmin):
    list_display = ['player', 'badge', 'tournament', 'awarded_at']
    list_filter = ['badge', 'awarded_at']
    search_fields = ['player__full_name', 'badge__name']

@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ['team', 'tournament', 'trophy_type', 'position', 'awarded_at']
    list_filter = ['trophy_type', 'awarded_at']
    search_fields = ['team__team_name', 'tournament__name']
