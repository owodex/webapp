from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *

@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:  # Only for newly created users
        Wallet.objects.create(user=instance)
