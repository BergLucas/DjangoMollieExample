from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.reverse import reverse

from rest_framework_extensions.mixins import NestedViewSetMixin

from django_filters.rest_framework import DjangoFilterBackend

from mollie.api.error import ResponseError, ResponseHandlingError

from orders.filters import ItemFilter, OrderDetailFilter, OrderFilter
from orders.serializers import OrderDetailSerializer, OrderSerializer, ItemSerializer, ShoppingCartSerializer
from orders.models import Order, Item, OrderDetail, Payment


@csrf_exempt
@api_view(("post",))
def update_payment(request: Request) -> HttpResponse:
    """This view allows to update a payment.

    Args:
    -----
        request (Request): The request.

    Returns:
    --------
        HttpResponse: An HTTP response.
    """
    id = request.POST.get("id")
    if id is not None:
        payment = Payment.objects.filter(id=id).first()
        if payment is not None:
            payment.update()

    return HttpResponse(status=200)


class PurchaseView(APIView):
    """This view allows to purchase a list of items."""

    http_method_names = ("post",)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request: Request) -> JsonResponse:
        """Handles the POST request that allows the current user to buy a list items.

        Args:
        -----
            request (Request): The request which contains the list of items.

        Raises:
        -------
            ValidationError: If the request is invalid.
            APIException: If there is an error with Mollie.

        Returns:
        --------
            JsonResponse: The response with the checkout url.
        """
        # Create a shopping cart serializer
        cart_serializer = ShoppingCartSerializer(data=request.data)

        cart_serializer.is_valid(raise_exception=True)

        # Process the shopping cart serializer data
        items = {}
        for item_info in cart_serializer.validated_data["items"]:
            item = Item.objects.get(id=item_info["item_id"])
            quantity = item_info["quantity"]

            if item in items:
                items[item] += quantity
            else:
                items[item] = quantity

        # Create the order
        order = Order.create_order(request.user, items)

        # Create the payment
        try:
            payment = Payment.create_payment(
                order=order,
                description=getattr(settings, "MOLLIE_DESCRIPTION_TEMPLATE").format(order_id=order.id),
                redirect_url=getattr(settings, "MOLLIE_REDIRECT_URL_TEMPLATE").format(order_id=order.id),
                webhook_url=getattr(settings, "MOLLIE_BASE_URL") + reverse("update_payment"),
                method=getattr(settings, "MOLLIE_PAYMENT_METHOD"),
            )
        except (ResponseError, ResponseHandlingError):
            order.delete()
            raise APIException()

        return JsonResponse({"checkout_url": payment.checkout_url})


class ReadOnlyOrderView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """This view allows to retrieve and list the current user's orders."""

    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = OrderSerializer

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = OrderFilter

    ordering_fields = ["date", "status"]

    def get_queryset(self) -> QuerySet:
        return self.filter_queryset_by_parents_lookups(self.request.user.orders.all())


class ReadOnlyOrderDetailView(viewsets.ReadOnlyModelViewSet, NestedViewSetMixin):
    """This view allows to retrieve and list the current user's order details."""

    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = OrderDetailSerializer

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = OrderDetailFilter

    ordering_fields = ["quantity"]

    def get_queryset(self) -> QuerySet:
        return self.filter_queryset_by_parents_lookups(
            OrderDetail.objects.filter(order__in=self.request.user.orders.all()).all()
        )


class ReadOnlyItemView(viewsets.ReadOnlyModelViewSet):
    """This view allows to retrieve and list the items."""

    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = ItemSerializer

    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = ItemFilter

    ordering_fields = ["name", "price"]

    queryset = Item.objects.all()
