from __future__ import annotations
from django.utils.translation import gettext_lazy
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.conf import settings
from django.db import models

from typing import Sequence, Optional

from decimal import Decimal
from datetime import datetime

from mollie.api.objects.payment import Payment as MolliePayment
from mollie.api.client import Client

class Item(models.Model):
    """This type represents an order item."""

    id = models.AutoField(null=False, primary_key=True)
    name = models.TextField(max_length=255, null=False)
    price = models.DecimalField(max_digits=20, decimal_places=2, null=False, validators=(MinValueValidator(0),))

    def __str__(self) -> str:
        """Returns the human-readable representation of `self`.

        Returns:
        --------
            str: The human-readable representation of `self`.
        """
        return repr(self)

    def __repr__(self) -> str:
        """Returns the representation of `self`.

        Returns:
        --------
            str: The representation of `self`.
        """
        return 'Item(id=%d, name="%s", price=%.2f)' % (self.id, self.name, self.price)


class Order(models.Model):
    """This type represents an order."""

    id = models.AutoField(null=False, primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING, related_name="orders")
    date = models.DateTimeField(null=False)

    @property
    def total(self) -> Decimal:
        """Returns the total price of `self`.

        Returns:
        --------
            Decimal: The total price of `self`.
        """
        result = 0
        for detail in self.details.all():
            result += detail.item.price * detail.quantity
        return result

    def __str__(self) -> str:
        """Returns the human-readable representation of `self`.

        Returns:
        --------
            str: The human-readable representation of `self`.
        """
        return 'Order(id=%d, user="%s")' % (self.id, self.user)

    def __repr__(self) -> str:
        """Returns the representation of `self`.

        Returns:
        --------
            str: The representation of `self`.
        """
        return "Order(id=%d, user=%s)" % (self.id, repr(self.user))

    @staticmethod
    def create_order(user: User, items: dict[Item, int]) -> Order:
        """Creates a new order and saves it in the database.

        Args:
        -----
            user (User): The user.
            items (dict[Item, int]): The dict of items and their quantities.

        Returns:
        --------
            Order: The new order.
        """
        order = Order(user=user, date=datetime.now())
        order.save()
        for item, quantity in items.items():
            order.details.create(item=item, quantity=quantity)
        order.save()
        return order


class Payment(models.Model):
    """This type represents a payment."""

    MOLLIE_CLIENT = Client()
    MOLLIE_CLIENT.set_api_key(getattr(settings, "MOLLIE_API_KEY"))

    class PaymentStatus(models.TextChoices):
        """This type represents a payment status."""

        OPEN = MolliePayment.STATUS_OPEN, gettext_lazy("Open")
        CANCELED = MolliePayment.STATUS_CANCELED, gettext_lazy("Canceled")
        PENDING = MolliePayment.STATUS_PENDING, gettext_lazy("Pending")
        AUTHORIZED = MolliePayment.STATUS_AUTHORIZED, gettext_lazy("Authorized")
        EXPIRED = MolliePayment.STATUS_EXPIRED, gettext_lazy("Expired")
        FAILED = MolliePayment.STATUS_FAILED, gettext_lazy("Failed")
        PAID = MolliePayment.STATUS_PAID, gettext_lazy("Paid")

    id = models.CharField(max_length=20, null=False, primary_key=True)
    order = models.OneToOneField(Order, models.DO_NOTHING, null=False, related_name="payment")
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.OPEN, null=False)
    checkout_url = models.URLField(null=False)

    def update(self) -> None:
        """Updates `self` in the database."""
        mollie_payment: MolliePayment = Payment.MOLLIE_CLIENT.payments.get(self.id)

        assert mollie_payment["metadata"] == self.order.id

        self.status = mollie_payment.status
        self.save()

    def __str__(self) -> str:
        """Returns the human-readable representation of `self`.

        Returns:
        --------
            str: The human-readable representation of `self`.
        """
        return 'Payment(id="%s", order=%d, status="%s")' % (
            self.id,
            self.order.id,
            self.status,
        )

    def __repr__(self) -> str:
        """Returns the representation of `self`.

        Returns:
        --------
            str: The representation of `self`.
        """
        return 'Payment(id="%s", order=%s, status="%s", checkout_url="%s")' % (
            self.id,
            repr(self.order),
            self.status,
            self.checkout_url,
        )

    @staticmethod
    def create_payment(
        order: Order,
        description: str,
        redirect_url: str,
        webhook_url: Optional[str] = None,
        method: Optional[str | Sequence[str]] = None,
    ) -> Payment:
        """Creates a new payment for an order and saves it in the database.

        Args:
        -----
            order (Order): The order.
            description (str): The order description.
            redirect_url (str): The redirection url.
            webhook_url (Optional[str], optional): The webhook url. Defaults to None
            method (Optional[str | Sequence[str]], optional): The method. Defaults to None

        Raises:
        -------
            ResponseError, ResponseHandlingError: If there is an error with Mollie.

        Returns:
        --------
            Payment: The new payment.
        """
        # Create the payment data
        data = {
            "amount": {"currency": "EUR", "value": "%.2f" % order.total},
            "description": description,
            "redirectUrl": redirect_url,
            "metadata": order.id,
        }

        if webhook_url is not None:
            data["webhookUrl"] = webhook_url
        if method is not None:
            data["method"] = method

        # Create the payment
        mollie_payment: MolliePayment = Payment.MOLLIE_CLIENT.payments.create(data)

        payment = Payment.objects.create(
            id=mollie_payment.id, order=order, status=mollie_payment.status, checkout_url=mollie_payment.checkout_url
        )
        payment.save()
        return payment


class OrderDetail(models.Model):
    """This type represents an order detail."""

    id = models.AutoField(null=False, primary_key=True)
    order = models.ForeignKey(Order, models.DO_NOTHING, null=False, related_name="details")
    item = models.ForeignKey(Item, models.DO_NOTHING, null=False, related_name="order_details")
    quantity = models.IntegerField(null=False, validators=(MinValueValidator(0),))

    def __str__(self) -> str:
        """Returns the human-readable representation of `self`.

        Returns:
        --------
            str: The human-readable representation of `self`.
        """
        return 'OrderDetail(id=%d, order=%d, item="%s", quantity=%d)' % (
            self.id,
            self.order.id,
            self.item.name,
            self.quantity,
        )

    def __repr__(self) -> str:
        """Returns the representation of `self`.

        Returns:
        --------
            str: The representation of `self`.
        """
        return "OrderDetail(id=%d, order=%s, item=%s, quantity=%d)" % (
            self.id,
            repr(self.order),
            repr(self.item),
            self.quantity,
        )
