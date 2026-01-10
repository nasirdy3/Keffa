from .models import Notification

def notifications_processor(request):
    """
    Adds unread notifications count to context.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        # Optional: fetch latest few to show in dropdown
        latest_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
        return {
            'unread_notifications_count': unread_count,
            'navbar_notifications': latest_notifications
        }
    return {
        'unread_notifications_count': 0,
        'navbar_notifications': []
    }
