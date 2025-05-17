from .models import AuditLog
from .utils import log_user_action


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            action_type = {
                "POST": AuditLog.ActionType.CREATE,
                "PUT": AuditLog.ActionType.UPDATE,
                "PATCH": AuditLog.ActionType.UPDATE,
                "DELETE": AuditLog.ActionType.DELETE,
            }.get(request.method, AuditLog.ActionType.VIEW)

            priority = {
                "POST": AuditLog.Priority.MEDIUM,
                "PUT": AuditLog.Priority.MEDIUM,
                "PATCH": AuditLog.Priority.MEDIUM,
                "DELETE": AuditLog.Priority.HIGH,
            }.get(request.method, AuditLog.Priority.LOW)

            log_user_action(
                request=request,
                action_type=action_type,
                status=(
                    AuditLog.Status.SUCCESS
                    if response.status_code < 400
                    else AuditLog.Status.FAILED
                ),
                priority=priority,
                notify=action_type == AuditLog.ActionType.DELETE,
            )

        return response
