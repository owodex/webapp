from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            users=request.user, is_read=False
        ).order_by('-created_at')[:5]  # Get the 5 most recent unread notifications
        return {'user_notifications': notifications}
    return {}