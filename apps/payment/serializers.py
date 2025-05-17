from rest_framework import serializers

from .models import Payment, PaymentGatewayConfig, Refund, Transaction


class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGatewayConfig
        fields = ["id", "name", "callback_url", "is_active", "created_at"]
        read_only_fields = ["created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    gateway = serializers.PrimaryKeyRelatedField(
        queryset=PaymentGatewayConfig.objects.filter(is_active=True)  # type: ignore
    )
    user = serializers.StringRelatedField()
    # billing_location = serializers.PrimaryKeyRelatedField(
    #     queryset=Location.objects.all(),  # type: ignore
    #     allow_null=True,
    # )

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "gateway",
            "amount",
            "currency",
            "status",
            "transaction_id",
            "qr_code",
            "content_type",
            "object_id",
            # "billing_location",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user",
            "status",
            "transaction_id",
            "qr_code",
            "created_at",
            "updated_at",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    payment = serializers.StringRelatedField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "payment",
            "status",
            "bank_response",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields


class RefundSerializer(serializers.ModelSerializer):
    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())  # type: ignore
    user = serializers.StringRelatedField()

    class Meta:
        model = Refund
        fields = [
            "id",
            "payment",
            "user",
            "amount",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "status", "created_at", "updated_at"]
