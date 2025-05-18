from celery import shared_task
from django.db import models
from django.utils import timezone
from django_pandas.io import read_frame

from apps.orders.models import Order, OrderItem

from .models import SalesReport


@shared_task
def generate_sales_report():
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=30)

    orders = Order.objects.filter(  # type: ignore
        created_at__range=(start_date, end_date), status="delivered"
    )
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=models.Sum("total_amount"))["total"] or 0
    average_order_value = total_revenue / total_orders if total_orders else 0

    order_items = OrderItem.objects.filter(order__in=orders)  # type: ignore
    top_products = (
        read_frame(order_items, fieldnames=["variant__product__name", "quantity"])
        .groupby("variant__product__name")
        .sum()
        .reset_index()
        .sort_values("quantity", ascending=False)
        .head(5)
        .to_dict("records")
    )

    SalesReport.objects.create(  # type: ignore
        start_date=start_date,
        end_date=end_date,
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_order_value=average_order_value,
        top_products=top_products,
    )
