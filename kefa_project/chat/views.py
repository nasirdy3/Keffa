from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from kefa_project.matches.models import FriendlyMatch

@login_required
def community_chat(request):
    # Fetch existing open friendlies to populate the list on page load
    open_friendlies = FriendlyMatch.objects.filter(
        status='open'
    ).select_related('created_by_team').order_by('-created_at')[:20]
    
    return render(request, 'chat/community.html', {
        'open_friendlies': open_friendlies
    })

