import json

from django.core.serializers import serialize
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action


@receiver(pre_save)
def log_model_update(sender, instance, **kwargs):
    if not hasattr(instance, "_audit_log_user"):
        return
    user = instance._audit_log_user
    if instance.pk:
        old_instance = sender.objects.filter(pk=instance.pk).first()
        if old_instance:
            old_data = json.loads(serialize("json", [old_instance]))[0]["fields"]
            new_data = json.loads(serialize("json", [instance]))[0]["fields"]
            changes = {
                k: {"old": old_data.get(k), "new": new_data.get(k)}
                for k in old_data
                if old_data.get(k) != new_data.get(k)
            }
            log_user_action(
                user=user,
                action_type=AuditLog.ActionType.UPDATE,
                content_object=instance,
                changes=changes,
                priority=AuditLog.Priority.MEDIUM,
            )


@receiver(post_save)
def log_model_create(sender, instance, created, **kwargs):
    if not created or not hasattr(instance, "_audit_log_user"):
        return
    user = instance._audit_log_user
    log_user_action(
        user=user,
        action_type=AuditLog.ActionType.CREATE,
        content_object=instance,
        priority=AuditLog.Priority.MEDIUM,
    )


@receiver(pre_delete)
def log_model_delete(sender, instance, **kwargs):
    if not hasattr(instance, "_audit_log_user"):
        return
    user = instance._audit_log_user
    data = json.loads(serialize("json", [instance]))[0]["fields"]
    log_user_action(
        user=user,
        action_type=AuditLog.ActionType.DELETE,
        content_object=instance,
        changes={"deleted": data},
        priority=AuditLog.Priority.HIGH,
        notify=True,
    )
