from __future__ import annotations
from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from orders.models import Order, OrderDetail, Item


class CartItemSerializer(serializers.Serializer):
    """This type represents a shopping cart item serializer."""

    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate_item_id(self, value: int) -> int:
        """Validates the item id.

        Args:
        -----
            value (int): The raw item id.

        Raises:
        -------
            serializers.ValidationError: If the item id is invalid.

        Returns:
        --------
            int: The validated item id.
        """
        if not Item.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Invalid item id : {value}")
        return value

    def validate_quantity(self, value: int) -> int:
        """Validates the quantity.

        Args:
        -----
            value (int): The raw quantity.

        Raises:
        -------
            serializers.ValidationError: If the quantity is invalid.

        Returns:
        --------
            int: The validated quantity.
        """
        if value <= 0:
            raise serializers.ValidationError(f"Invalid quantity : {value}")
        return value


class ShoppingCartSerializer(serializers.Serializer):
    """This type represents a shopping cart serializer."""

    items = CartItemSerializer(many=True)

    def validate_items(self, value: list[CartItemSerializer]) -> list[CartItemSerializer]:
        """Validates the items.

        Args:
        -----
            value (list[CartItemSerializer]): The raw items.

        Raises:
        -------
            serializers.ValidationError: If items is empty.

        Returns:
        --------
            list[CartItemSerializer]: The validated items.
        """
        if len(value) == 0:
            raise serializers.ValidationError(f"items is empty")
        return value


class ItemSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """This type represents an item serializer."""

    item_id = serializers.IntegerField(source="id")

    class Meta:
        model = Item
        fields = ("item_id", "name", "price")


class OrderDetailSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """This type represents an order detail serializer."""

    detail_id = serializers.IntegerField(source="id")
    item = ItemSerializer()

    class Meta:
        model = OrderDetail
        fields = ("detail_id", "item", "quantity")


class OrderSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """This type represents an order serializer."""

    order_id = serializers.IntegerField(source="id")
    total = serializers.DecimalField(20, 2)
    status = serializers.CharField(source="payment.status")
    checkout_url = serializers.URLField(source="payment.checkout_url")

    class Meta:
        model = Order
        fields = ("order_id", "total", "date", "status", "checkout_url")
