from django.contrib import admin
from orders.models import Item, Order, OrderDetail, Payment


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """This type allows to customize the items in the admin page."""

    list_display = ("id", "name", "price")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """This type allows to customize the orders in the admin page."""

    list_display = ("id", "user", "date")


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    """This type allows to customize the order details in the admin page."""

    list_display = ("id", "order", "item", "quantity")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """This type allows to customize the payments in the admin page."""

    list_display = ("id", "order", "status")
