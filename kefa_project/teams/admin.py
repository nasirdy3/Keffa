from django.contrib import admin
from .models import Team

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'player', 'created_at']
    search_fields = ['team_name', 'player__full_name']
    readonly_fields = ['created_at', 'updated_at']
