import json

from azbankgateways import models as bank_models
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AdminTextInputWidget
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.audit_log.models import AuditLog
from apps.audit_log.utils import log_user_action
from apps.notifications.utils import send_notification

from .models import Payment, PaymentGatewayConfig, Refund, Transaction
from .utils import verify_payment


class PaymentDateRangeFilter(SimpleListFilter):
    title = _("Created Date Range")
    parameter_name = "created_at_range"

    def lookups(self, request, model_admin):
        return (
            ("today", _("Today")),
            ("week", _("This Week")),
            ("month", _("This Month")),
        )

    def queryset(self, request, queryset):
        from datetime import timedelta

        from django.utils import timezone

        today = timezone.now().date()
        if self.value() == "today":
            return queryset.filter(created_at__date=today)
        elif self.value() == "week":
            return queryset.filter(created_at__date__gte=today - timedelta(days=7))
        elif self.value() == "month":
            return queryset.filter(created_at__date__gte=today - timedelta(days=30))
        return queryset


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "callback_url", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "is_active", "callback_url"),
            },
        ),
        (
            _("Credentials"),
            {
                "fields": ("merchant_id", "api_key"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at",),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):  # type: ignore
        form = super().get_form(request, obj, **kwargs)
        for field_name in ("merchant_id", "api_key"):
            if field_name in form.base_fields:  # type: ignore
                form.base_fields[field_name].widget = AdminTextInputWidget()  # type: ignore
        return form

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_user_action(
            request=request,
            user=request.user,
            action_type=(
                AuditLog.ActionType.UPDATE if change else AuditLog.ActionType.CREATE
            ),
            content_object=obj,
            priority=AuditLog.Priority.HIGH,
            notify=True,
        )


class TransactionInline(admin.TabularInline):
    model = Transaction
    fields = ("status", "bank_response_formatted", "error_message", "created_at")
    readonly_fields = (
        "status",
        "bank_response_formatted",
        "error_message",
        "created_at",
    )
    can_delete = False
    extra = 0

    def bank_response_formatted(self, obj):
        return format_html(
            "<pre>{}</pre>", json.dumps(obj.bank_response, indent=2, ensure_ascii=False)
        )

    bank_response_formatted.short_description = _("Bank Response")  # type: ignore


class RefundInline(admin.TabularInline):
    model = Refund
    fields = ("amount", "reason", "status", "created_at", "approve_refund_action")
    readonly_fields = (
        "amount",
        "reason",
        "status",
        "created_at",
        "approve_refund_action",
    )
    can_delete = False
    extra = 0

    def approve_refund_action(self, obj):
        if obj.status == "PENDING":
            return format_html(
                '<a class="button" href="{}">{}</a>',
                reverse("admin:approve_refund", args=[obj.pk]),
                _("Approve Refund"),
            )
        return "-"

    approve_refund_action.short_description = _("Action")  # type: ignore


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "user",
        "amount",
        "currency",
        "status",
        "gateway",
        "created_at",
        "qr_code_display",
    )
    list_filter = (
        "status",
        "currency",
        "gateway",
        PaymentDateRangeFilter,
    )
    search_fields = (
        "transaction_id",
        "user__username",
        "user__email",
    )
    readonly_fields = (
        "transaction_id",
        "token",
        "qr_code_display",
        "created_at",
        "updated_at",
        "metadata_formatted",
        "content_object_link",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "gateway",
                    "amount",
                    "currency",
                    "status",
                    "transaction_id",
                    "token",
                ),
            },
        ),
        (
            _("Related Object"),
            {
                "fields": ("content_type", "object_id", "content_object_link"),
            },
        ),
        # (
        #     _("Additional Info"),
        #     {
        #         "fields": ("billing_location", "qr_code_display", "metadata_formatted"),
        #     },
        # ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
    inlines = [TransactionInline, RefundInline]
    actions = ["retry_verification", "send_payment_notification"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "gateway")  # , "billing_location")
        )

    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="100" height="100" />', obj.qr_code.url
            )
        return "-"

    qr_code_display.short_description = _("QR Code")  # type: ignore

    def metadata_formatted(self, obj):
        return format_html(
            "<pre>{}</pre>", json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        )

    metadata_formatted.short_description = _("Metadata")  # type: ignore

    def content_object_link(self, obj):
        if obj.content_object:
            url = reverse(
                f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change",
                args=[obj.object_id],
            )
            return format_html('<a href="{}">{}</a>', url, obj.content_object)
        return "-"

    content_object_link.short_description = _("Related Object")  # type: ignore

    @admin.action(description=_("Retry payment verification"))
    def retry_verification(self, request, queryset):
        success_count = 0
        for payment in queryset:
            try:
                tracking_code = payment.transaction_id
                bank_record = bank_models.Bank.objects.get(tracking_code=tracking_code)
                if bank_record.status in ["RETURN_FROM_BANK", "EXPIRE_VERIFY_PAYMENT"]:
                    is_success = verify_payment(payment, tracking_code)
                    if is_success:
                        success_count += 1
                    log_user_action(
                        request=request,
                        user=request.user,
                        action_type=AuditLog.ActionType.SYSTEM,
                        content_object=payment,
                        priority=AuditLog.Priority.HIGH,
                        status=(
                            AuditLog.Status.SUCCESS
                            if is_success
                            else AuditLog.Status.FAILED
                        ),
                        notify=True,
                    )
            except (bank_models.Bank.DoesNotExist, Exception) as e:  # type: ignore
                log_user_action(
                    request=request,
                    user=request.user,
                    action_type=AuditLog.ActionType.SYSTEM,
                    status=AuditLog.Status.FAILED,
                    content_object=payment,
                    priority=AuditLog.Priority.HIGH,
                    error_message=str(e),
                    notify=True,
                )
        self.message_user(
            request, _(f"{success_count} payments verified successfully.")
        )

    @admin.action(description=_("Send payment status notification"))
    def send_payment_notification(self, request, queryset):
        for payment in queryset:
            message = (
                f"وضعیت پرداخت {payment.transaction_id}: {payment.get_status_display()}"
            )
            send_notification(
                user=payment.user,
                message=message,
                category="payment",
                priority="MED",  # type: ignore
                channels=["IN_APP", "WEBSOCKET", "EMAIL"],
                metadata={"payment_id": payment.id},
            )
            log_user_action(
                request=request,
                user=request.user,
                action_type=AuditLog.ActionType.SYSTEM,
                content_object=payment,
                priority=AuditLog.Priority.MEDIUM,
                metadata={"notification_sent": True},
            )
        self.message_user(
            request, _(f"Notifications sent for {queryset.count()} payments.")
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "refund/<int:pk>/approve/",
                self.admin_site.admin_view(self.approve_refund),
                name="approve_refund",
            ),
        ]
        return custom_urls + urls

    def approve_refund(self, request, pk):
        try:
            refund = Refund.objects.get(pk=pk)  # type: ignore
            if refund.status != "PENDING":
                self.message_user(request, _("Refund is not pending."), level="error")  # type: ignore
                return redirect("admin:payment_refund_change", refund.pk)

            refund.status = "APPROVED"
            refund.payment.status = Payment.Status.REFUNDED
            refund.payment.save()
            refund.save()

            send_notification(
                user=refund.user,
                message=f"درخواست بازگشت وجه برای {refund.amount} تأیید شد.",
                category="payment",
                priority="HIGH",  # type: ignore
                channels=["IN_APP", "WEBSOCKET", "EMAIL"],
                metadata={"refund_id": refund.id},
            )
            log_user_action(
                request=request,
                user=request.user,
                action_type=AuditLog.ActionType.UPDATE,
                content_object=refund,
                priority=AuditLog.Priority.HIGH,
                notify=True,
            )
            self.message_user(request, _("Refund approved successfully."))
        except Refund.DoesNotExist:  # type: ignore
            self.message_user(request, _("Refund not found."), level="error")  # type: ignore
        except Exception as e:
            self.message_user(request, _(f"Error: {str(e)}"), level="error")  # type: ignore
            log_user_action(
                request=request,
                user=request.user,
                action_type=AuditLog.ActionType.UPDATE,
                status=AuditLog.Status.FAILED,
                content_object=refund,  # type: ignore
                priority=AuditLog.Priority.HIGH,
                error_message=str(e),
                notify=True,
            )
        return redirect("admin:payment_refund_changelist")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("payment", "status", "created_at", "bank_response_formatted")
    list_filter = ("status", "created_at")
    search_fields = ("payment__transaction_id",)
    readonly_fields = (
        "payment",
        "status",
        "bank_response_formatted",
        "error_message",
        "created_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": ("payment", "status", "error_message"),
            },
        ),
        (
            _("Bank Response"),
            {
                "fields": ("bank_response_formatted",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at",),
            },
        ),
    )

    def bank_response_formatted(self, obj):
        return format_html(
            "<pre>{}</pre>", json.dumps(obj.bank_response, indent=2, ensure_ascii=False)
        )

    bank_response_formatted.short_description = _("Bank Response")  # type: ignore

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "user",
        "amount",
        "status",
        "created_at",
        "approve_refund_action",
    )
    list_filter = ("status", "created_at")
    search_fields = ("payment__transaction_id", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "approve_refund_action")
    fieldsets = (
        (
            None,
            {
                "fields": ("payment", "user", "amount", "reason", "status"),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def approve_refund_action(self, obj):
        if obj.status == "PENDING":
            return format_html(
                '<a class="button" href="{}">{}</a>',
                reverse("admin:approve_refund", args=[obj.pk]),
                _("Approve Refund"),
            )
        return "-"

    approve_refund_action.short_description = _("Action")  # type: ignore

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_user_action(
            request=request,
            user=request.user,
            action_type=(
                AuditLog.ActionType.UPDATE if change else AuditLog.ActionType.CREATE
            ),
            content_object=obj,
            priority=AuditLog.Priority.HIGH,
            notify=True,
        )
