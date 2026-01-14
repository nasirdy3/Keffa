from django.contrib import admin
from .models import Match, MatchPostponement, FriendlyMatch

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'tournament', 'match_date', 'match_time', 'status']
    list_filter = ['status', 'tournament', 'match_date']
    search_fields = ['home_team__team_name', 'away_team__team_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Match Details', {
            'fields': ('tournament', 'home_team', 'away_team', 'match_date', 'match_time', 'status')
        }),
        ('Scores & Verification', {
            'fields': ('home_score', 'away_score', 'verified_at', 'verified_by')
        }),
        ('Match Summary', {
            'fields': ('match_summary', 'summary_image', 'summary_video'),
            'classes': ('collapse',),
            'description': 'Add a written summary and media attachments for completed matches.'
        }),
        ('Technical Info', {
            'fields': ('home_ready', 'away_ready', 'ready_time_start', 'game_code', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MatchPostponement)
class MatchPostponementAdmin(admin.ModelAdmin):
    list_display = ['match', 'requested_by', 'status', 'proposed_date', 'proposed_time']
    list_filter = ['status', 'created_at']
    search_fields = ['match__home_team__team_name', 'match__away_team__team_name']

@admin.register(FriendlyMatch)
class FriendlyMatchAdmin(admin.ModelAdmin):
    list_display = ['created_by_team', 'opponent_team', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['created_by_team__team_name', 'opponent_team__team_name']
