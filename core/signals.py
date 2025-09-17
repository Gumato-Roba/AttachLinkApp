# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.conf import settings
# from .models import Company

# User = settings.AUTH_USER_MODEL  # This ensures we use your custom User model

# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_related_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.role == 'company':
#             Company.objects.create(user=instance)
      
