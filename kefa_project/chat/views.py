from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from kefa_project.matches.models import FriendlyMatch

@login_required
def community_chat(request):
    from .models import ChatMessage
    
    # Fetch existing open friendlies to populate the list on page load
    open_friendlies = FriendlyMatch.objects.filter(
        status='open'
    ).select_related('created_by_team').order_by('-created_at')[:20]
    
    # Fetch recent chat history
    recent_messages = ChatMessage.objects.select_related('user').order_by('-timestamp')[:50]
    # Reverse locally so they appear in correct chronological order in the chat window (standard chat behavior)
    recent_messages = reversed(list(recent_messages))
    
    return render(request, 'chat/community.html', {
        'open_friendlies': open_friendlies,
        'recent_messages': recent_messages
    })

