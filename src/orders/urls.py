from django.urls import path
from rest_framework_extensions.routers import ExtendedSimpleRouter
from orders.views import (
    PurchaseView,
    ReadOnlyItemView,
    ReadOnlyOrderDetailView,
    ReadOnlyOrderView,
    update_payment,
)

router = ExtendedSimpleRouter()

router.register("items", ReadOnlyItemView, basename="item")

orders = router.register("orders", ReadOnlyOrderView, basename="order")
orders.register("details", ReadOnlyOrderDetailView, basename="orders-detail", parents_query_lookups=("order",))

urlpatterns = router.urls + [
    path("purchase/", PurchaseView.as_view()),
    path("update/payment/", update_payment, name="update_payment"),
]
