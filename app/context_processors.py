from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            users=request.user, is_read=False
        ).order_by('-created_at')[:5]  # Get the 5 most recent unread notifications
        
        # Get the count of unread notifications
        unread_count = notifications.count()
        
        return {
            'user_notifications': notifications,
            'unread_notification_count': unread_count
        }
    return {}