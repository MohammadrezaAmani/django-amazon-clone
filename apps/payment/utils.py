import logging

from azbankgateways import bankfactories
from azbankgateways import models as bank_models
from azbankgateways.exceptions import AZBankGatewaysException
from django.urls import reverse

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification

from .models import Payment, Transaction

logger = logging.getLogger(__name__)


def initiate_payment(payment, request):
    """Initiate a payment with the selected gateway."""
    factory = bankfactories.BankFactory()
    try:
        bank = factory.auto_create()
        bank.set_request(request)
        bank.set_amount(int(payment.amount))
        bank.set_client_callback_url(
            request.build_absolute_uri(reverse("payment:callback"))
        )
        bank.set_mobile_number(
            payment.user.phone_number or "+989000000000"
        )  # Fallback phone

        bank_record = bank.ready()
        payment.token = bank_record.token  # type: ignore
        payment.transaction_id = bank_record.tracking_code
        payment.save()

        Transaction.objects.create(  # type: ignore
            payment=payment,
            status=Transaction.Status.INITIATED,
            bank_response={
                "token": bank_record.token,  # type: ignore
                "tracking_code": bank_record.tracking_code,
            },
        )

        log_user_action(
            request=request,
            user=payment.user,
            action_type=AuditLog.ActionType.CREATE,
            content_object=payment,
            priority=AuditLog.Priority.MEDIUM,
            metadata={"gateway": bank_record.bank_type},
        )

        return bank.get_gateway()
    except AZBankGatewaysException as e:
        logger.error(f"Payment initiation failed: {str(e)}")
        Transaction.objects.create(  # type: ignore
            payment=payment,
            status=Transaction.Status.FAILED,
            error_message=str(e),
        )
        log_user_action(
            request=request,
            user=payment.user,
            action_type=AuditLog.ActionType.CREATE,
            status=AuditLog.Status.FAILED,
            content_object=payment,
            priority=AuditLog.Priority.HIGH,
            error_message=str(e),
            notify=True,
        )
        raise


def verify_payment(payment, tracking_code):
    """Verify payment status with the gateway."""
    try:
        bank_record = bank_models.Bank.objects.get(tracking_code=tracking_code)
        factory = bankfactories.BankFactory()
        bank = factory.create(
            bank_type=bank_record.bank_type,
            identifier=bank_record.bank_choose_identifier,
        )
        bank.verify(tracking_code)

        bank_record.refresh_from_db()
        payment.status = (
            Payment.Status.SUCCESS if bank_record.is_success else Payment.Status.FAILED
        )
        payment.save()

        transaction_status = (
            Transaction.Status.COMPLETED
            if bank_record.is_success
            else Transaction.Status.FAILED
        )
        Transaction.objects.create(  # type: ignore
            payment=payment,
            status=transaction_status,
            bank_response={
                "tracking_code": tracking_code,
                "is_success": bank_record.is_success,
                "bank_response": bank_record.bank_response,
            },
            error_message="" if bank_record.is_success else bank_record.status,
        )

        if bank_record.is_success:
            send_notification(
                user=payment.user,
                message=f"پرداخت {payment.transaction_id} با موفقیت انجام شد.",
                category="payment",
                priority="MED",  # type: ignore
                channels=["IN_APP", "WEBSOCKET", "EMAIL"],
                metadata={"payment_id": payment.id},
            )
            log_user_action(
                user=payment.user,
                action_type=AuditLog.ActionType.UPDATE,
                content_object=payment,
                priority=AuditLog.Priority.MEDIUM,
                metadata={"status": "SUCCESS"},
            )
        else:
            send_notification(
                user=payment.user,
                message=f"پرداخت {payment.transaction_id} ناموفق بود.",
                category="payment",
                priority="HIGH",  # type: ignore
                channels=["IN_APP", "WEBSOCKET", "EMAIL"],
                metadata={"payment_id": payment.id},
            )
            log_user_action(
                user=payment.user,
                action_type=AuditLog.ActionType.UPDATE,
                status=AuditLog.Status.FAILED,
                content_object=payment,
                priority=AuditLog.Priority.HIGH,
                error_message=bank_record.status,
                notify=True,
            )

        return bank_record.is_success
    except (bank_models.Bank.DoesNotExist, AZBankGatewaysException) as e:  # type: ignore
        logger.error(f"Payment verification failed: {str(e)}")
        payment.status = Payment.Status.FAILED
        payment.save()
        Transaction.objects.create(  # type: ignore
            payment=payment,
            status=Transaction.Status.FAILED,
            error_message=str(e),
        )
        log_user_action(
            user=payment.user,
            action_type=AuditLog.ActionType.UPDATE,
            status=AuditLog.Status.FAILED,
            content_object=payment,
            priority=AuditLog.Priority.HIGH,
            error_message=str(e),
            notify=True,
        )
        return False
