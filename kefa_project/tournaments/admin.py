from django.contrib import admin
from django.contrib import messages
from .models import Tournament, TournamentRegistration, Standing
from .services import lock_and_generate_fixtures, regenerate_fixtures

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament_type', 'round_robin_type', 'priority', 'status', 'current_teams_count', 'team_limit', 'start_date', 'end_date', 'match_frequency', 'fixtures_generated']
    list_filter = ['tournament_type', 'status', 'start_date', 'match_frequency', 'priority', 'round_robin_type']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'current_teams_count', 'allowed_weekdays']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'tournament_type', 'team_limit', 'priority', 'registration_fee', 'prize', 'rules', 'status')
        }),
        ('Scheduling', {
            'fields': (
                'start_date', 'end_date', 'default_match_time', 
                'match_frequency', 'matches_per_day', 
                'round_robin_type',
                'allowed_weekdays',
                'auto_schedule_enabled', 'fixtures_generated'
            )
        }),
        ('Advanced', {
            'fields': ('junior_league', 'promotion_relegation_enabled', 'teams_to_promote', 'teams_to_relegate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'current_teams_count'),
            'classes': ('collapse',)
        }),
    )
    actions = ['generate_fixtures_action', 'preview_schedule_action', 'safe_regenerate_fixtures']
    
    def generate_fixtures_action(self, request, queryset):
        """Generate fixtures for selected tournaments"""
        for tournament in queryset:
            if tournament.fixtures_generated:
                self.message_user(request, f"{tournament.name}: Fixtures already generated. Use 'Safe Regenerate' instead.", level=messages.WARNING)
                continue
            
            if tournament.current_teams_count < 2:
                self.message_user(request, f"{tournament.name}: Need at least 2 teams to generate fixtures.", level=messages.ERROR)
                continue
            
            # Validate scheduling feasibility
            is_feasible, message = tournament.validate_scheduling_feasibility()
            if not is_feasible:
                self.message_user(request, f"{tournament.name}: {message}", level=messages.ERROR)
                continue
            
            try:
                lock_and_generate_fixtures(tournament)
                tournament.fixtures_generated = True
                tournament.save()
                self.message_user(request, f"{tournament.name}: Fixtures generated successfully!", level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"{tournament.name}: Error generating fixtures - {str(e)}", level=messages.ERROR)
    
    generate_fixtures_action.short_description = "Generate Fixtures for Selected Tournaments"
    
    def preview_schedule_action(self, request, queryset):
        """Preview fixture schedule without generating"""
        for tournament in queryset:
            is_feasible, message = tournament.validate_scheduling_feasibility()
            total_matches = tournament.calculate_total_matches()
            
            if tournament.end_date:
                date_range = (tournament.end_date - tournament.start_date).days + 1
                self.message_user(
                    request, 
                    f"{tournament.name}: {total_matches} matches needed | {date_range} days available | {message}",
                    level=messages.INFO if is_feasible else messages.WARNING
                )
            else:
                self.message_user(
                    request,
                    f"{tournament.name}: {total_matches} matches needed | No end date specified",
                    level=messages.INFO
                )
    
    preview_schedule_action.short_description = "Preview Fixture Schedule"
    
    def safe_regenerate_fixtures(self, request, queryset):
        """Safely regenerate fixtures (only if no matches have started)"""
        for tournament in queryset:
            try:
                regenerate_fixtures(tournament)
                self.message_user(request, f"{tournament.name}: Fixtures regenerated successfully!", level=messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"{tournament.name}: Cannot regenerate - {str(e)}", level=messages.ERROR)
    
    safe_regenerate_fixtures.short_description = "Safely Regenerate Fixtures"

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
