from orders.models import Order, OrderDetail, Item
import django_filters


class ItemFilter(django_filters.FilterSet):
    """This type represents an item filter."""

    class Meta:
        model = Item
        fields = {
            "name": ("exact", "iexact", "contains", "icontains", "startswith", "istartswith"),
            "price": ("exact", "lt", "gt"),
        }


class OrderDetailFilter(django_filters.FilterSet):
    """This type represents an order detail filter."""

    class Meta:
        model = OrderDetail
        fields = {"quantity": ("exact", "lt", "gt")}


class OrderFilter(django_filters.FilterSet):
    """This type represents an order filter."""

    status = django_filters.CharFilter(field_name="payment__status", lookup_expr="exact")

    class Meta:
        model = Order
        fields = {"date": ("exact", "lt", "gt")}
