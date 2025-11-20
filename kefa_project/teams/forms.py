from django import forms
from .models import Team

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['team_name', 'logo', 'squad_image']
        help_texts = {
            'squad_image': 'Upload an image of your eFootball squad (required)',
            'logo': 'Upload your team logo (optional)',
        }
