from django.contrib import admin
from .models import Highlight

@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ['match', 'uploaded_by_team', 'uploaded_by_side', 'status', 'uploaded_at']
    list_filter = ['status', 'uploaded_by_side', 'uploaded_at']
    search_fields = ['match__home_team__team_name', 'match__away_team__team_name', 'uploaded_by_team__team_name']
    readonly_fields = ['uploaded_at', 'verified_at']
