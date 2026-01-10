from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Notification

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Mark all as read when visiting the full list page? Or just show them?
    # Usually users prefer manual clear or mark read on click. 
    # Let's keep them unread until clicked or "Mark All Read" button used.
    
    return render(request, 'notifications/list.html', {
        'notifications': notifications
    })

@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
        
    return redirect(notification.link) if notification.link else redirect('notifications:list')

@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('notifications:list')
