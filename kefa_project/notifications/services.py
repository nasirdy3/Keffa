from .models import Notification

def create_notification(recipient, title, message, notification_type='system', link=''):
    """
    Creates a new notification for a user.
    """
    try:
        Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link
        )
        return True
    except Exception as e:
        # Log error but don't crash application flow
        print(f"Error creating notification: {e}")
        return False
