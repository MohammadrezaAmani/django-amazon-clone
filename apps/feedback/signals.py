# from django.db.models.signals import post_save
# from django.dispatch import receiver

# from .models import Feedback
# from .tasks import notify_admins_on_feedback


# @receiver(post_save, sender=Feedback)
# def notify_admins_on_new_feedback(sender, instance, created, **kwargs):
#     if created:
#         notify_admins_on_feedback.delay(instance.id)  # type: ignore
