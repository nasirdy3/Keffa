from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Badge, PlayerBadge

@login_required
def gallery(request):
    """
    Displays all available badges and highlights the ones the user has earned.
    """
    player = request.user.player_profile
    all_badges = Badge.objects.all()
    
    # Get IDs of badges the player has earned
    earned_ids = PlayerBadge.objects.filter(player=player).values_list('badge_id', flat=True)
    
    return render(request, 'achievements/gallery.html', {
        'all_badges': all_badges,
        'earned_ids': earned_ids
    })
