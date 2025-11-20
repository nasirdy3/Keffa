from django.contrib import admin
from .models import Tournament, TournamentRegistration, Standing

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament_type', 'status', 'current_teams_count', 'team_limit', 'start_date']
    list_filter = ['tournament_type', 'status', 'start_date']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'current_teams_count']

@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'team', 'payment_verified', 'registered_at']
    list_filter = ['payment_verified', 'tournament']
    search_fields = ['team__team_name', 'tournament__name']

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ['team', 'tournament', 'played', 'won', 'drawn', 'lost', 'points', 'goal_difference']
    list_filter = ['tournament']
    search_fields = ['team__team_name']
    readonly_fields = ['goal_difference']
