from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Cart

@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    if created or not Cart.objects.filter(user=instance).exists():
        Cart.objects.get_or_create(user=instance)
