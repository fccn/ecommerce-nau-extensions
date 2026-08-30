"""
Basket billing information views.
"""
import logging
from abc import abstractmethod

from django import shortcuts
from django.contrib import messages
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from edx_django_utils.monitoring import set_custom_attribute
from nau_extensions.forms import (BasketBillingInformationAddressForm,
                                  BasketBillingInformationVATINForm)
from nau_extensions.models import BasketBillingInformation
from nau_extensions.serializers import OrderReceiptLinkSerializer
from nau_extensions.utils import get_default_country
from oscar.apps.payment.exceptions import GatewayError, PaymentError
from oscar.core.loading import get_class, get_model
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ecommerce.extensions.api.permissions import IsStaffOrOwner
from ecommerce.extensions.api.throttles import ServiceUserThrottle
from ecommerce.extensions.fulfillment.status import ORDER

logger = logging.getLogger(__name__)

# Monitoring attribute reporting how `OrderPaymentStatusView` resolved the payment
# of a pending order. See `OrderPaymentStatusView._resolve` for its values.
RESOLUTION_ATTRIBUTE = "nau_order_payment_resolution"

UserAddress = get_model("address", "UserAddress")
Basket = get_model("basket", "Basket")
Order = get_model('order', 'Order')
PaymentProcessorResponse = get_model("payment", "PaymentProcessorResponse")

AbstractAddressForm = get_class("address.forms", "AbstractAddressForm")


class BasketBillingInformationCreateUpdateView(generic.UpdateView):
    """
    The merged create and update view for the `BasketBillingInformation`.
    """
    success_url = "/basket/"

    def get_object(self, queryset=None):
        try:
            return BasketBillingInformation.objects.get(  # pylint: disable=unused-variable
                basket=self.basket
            )
        except BasketBillingInformation.DoesNotExist:
            return BasketBillingInformation(country=get_default_country())

    def get(self, request, *args, **kwargs):
        self.basket = shortcuts.get_object_or_404(  # pylint: disable=attribute-defined-outside-init
            Basket, pk=request.GET.get("basket_id")
        )
        if self.basket.owner != request.user:
            return HttpResponseForbidden("You need to be the owner of the Basket")
        if hasattr(self.basket, "order"):
            return HttpResponse(
                "You can't change the billing information of a basket already ordered",
                status=409,
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.basket = shortcuts.get_object_or_404(  # pylint: disable=attribute-defined-outside-init
            Basket, pk=request.POST.get("basket_id")
        )
        if self.basket.owner != request.user:
            return HttpResponseForbidden("You need to be the owner of the Basket")
        if hasattr(self.basket, "order"):
            return HttpResponse(
                "You can't change the billing information of a basket already ordered",
                status=409,
            )
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["basket"] = self.basket
        return kwargs

    def get_initial(self):
        """
        Load previous basket billing information from previous basket of same owner, load only
        some fields related to the form.
        """
        _dict = super().get_initial()
        data = {}

        def get_attrs(_object, attrs=[]):  # pylint: disable=dangerous-default-value
            """
            If the object has any attributes.

            Returns:
                data (dict): the key - value of the attributes and its value.
            """
            data = {}
            if _object:
                for attr in attrs:
                    value = getattr(_object, attr)
                    if value:
                        data[attr] = value
            return data

        def _previous_bbi(basket):
            """
            Get the previous BasketBillingInformation for a previous basket of the requested user.
            """
            return (
                BasketBillingInformation.objects.filter(basket__owner=basket.owner)
                .exclude(basket=basket)
                .select_related("basket")
                .order_by("-basket__id")
                .first()
            )

        bbi = None
        try:
            bbi = BasketBillingInformation.objects.get(basket=self.basket)
        except BasketBillingInformation.DoesNotExist:
            pass

        data = get_attrs(bbi, self.get_fields_decide_which_bbi_to_use())
        if len(data) == 0:
            bbi = _previous_bbi(self.basket)

        if bbi:
            data = get_attrs(bbi, self.get_initial_fields())

        return {**_dict, **data}

    @abstractmethod
    def get_initial_fields(self):
        """
        The fields that are going to be used on the `get_initial` method, used to pre-populate the
        form.
        """
        pass  # pylint: disable=unnecessary-pass

    def get_fields_decide_which_bbi_to_use(self):
        """
        The fields that we use do decide witch BasketBillingInformation should we use.
        We need this, because the country field is shared between Address and VATIN.
        """
        fields = self.get_initial_fields()
        fields.remove("country")
        return fields


class BasketBillingInformationAddressCreateUpdateView(
    BasketBillingInformationCreateUpdateView, AbstractAddressForm
):
    """
    Create or Update an address on the basket billing information object.
    """

    template_name = "nau_extensions/checkout/basket_billing_information/address.html"
    form_class = BasketBillingInformationAddressForm

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return super().get_success_url()

    def get_initial_fields(self):
        """
        The fields from the address that are going to prepopulate the form.
        """
        return [
            "title",
            "first_name",
            "last_name",
            "line1",
            "line2",
            "line3",
            "line4",
            "state",
            "postcode",
            "country",
        ]


class BasketBillingInformationVATINCreateUpdateView(
    BasketBillingInformationCreateUpdateView
):
    """
    Create an Basket Billing Information
    """

    template_name = "nau_extensions/checkout/basket_billing_information/vatin.html"
    form_class = BasketBillingInformationVATINForm

    def get_initial_fields(self):
        """
        The fields that are going to prepopulate the form.
        """
        return ["country", "vatin"]

    def get_success_url(self):
        messages.info(self.request, _("VATIN saved"))
        return super().get_success_url()


@method_decorator(transaction.non_atomic_requests, name='dispatch')
class ReceiptLinkView(APIView):
    """
    API GET /payment/nau_extensions/receipt-link
    """
    permission_classes = (IsAuthenticated, IsStaffOrOwner,)
    throttle_classes = (ServiceUserThrottle,)

    def get(self, request):
        order_id = request.query_params.get('order_id')
        logger.info("Getting receipt_link of Order id=[%s]", order_id)
        if order_id:
            query_set = Order.objects.filter(id=order_id)
            user = self.request.user
            if not user.is_staff:
                query_set = query_set.filter(user=user)
            order = shortcuts.get_object_or_404(Order, id=order_id)
            if not user.is_staff and order.user != user:
                raise PermissionDenied
            serializer = OrderReceiptLinkSerializer(order)
            receipt_link = serializer.data['receipt_link']
            logging.info("For Order id=[%s] returning receipt_link=[%s]", order_id, receipt_link)
            return HttpResponse(receipt_link if receipt_link else '')
        raise Http404("No id parameter found")


class OrderPaymentStatusView(APIView):
    """
    API GET /payment/nau_extensions/order-payment-status/?order_number=OPENEDX-100012

    Lazily resolves the payment status of a single order.

    Asynchronous payment methods -- on NAU, the Multibanco reference (`REFMB`) --
    are not confirmed while the user is still in the browser: PayGate hands out a
    reference that can be paid days later. When the user comes back from PayGate an
    order is placed in the `Pending` status, unpaid and unfulfilled, so the payment
    is visible on the Order History page.

    This endpoint is what turns a `Pending` order into a paid one. There is no
    background job and no polling: the Order History page calls this once per
    pending row when the user opens it, and it runs exactly the same
    `handle_payment` the synchronous checkout flow runs.

    The `status` returned is the ecommerce order status, so it shares a vocabulary
    with the `status` field of `/api/v2/orders/`:

      * ``Complete``      : paid and fulfilled.
      * ``Open``          : paid, fulfilment pending or failed.
      * ``Pending``       : PayGate has not confirmed the payment yet.
      * ``Payment Error`` : the payment failed and will not resolve itself.

    Only the order owner (or a staff user) may query it.
    """

    permission_classes = (IsAuthenticated, IsStaffOrOwner,)
    throttle_classes = (ServiceUserThrottle,)

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, request, *args, **kwargs):
        """
        Disable atomicity for this view. Fulfilment is triggered from here and, as
        in the checkout views, the order has to be committed before the fulfilment
        tasks run.
        """
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        order_number = request.query_params.get("order_number")
        if not order_number:
            raise Http404("Missing 'order_number' query parameter")

        order = Order.objects.filter(number=order_number).first()
        if not order:
            raise Http404(f"No order found for order_number [{order_number}]")

        # `IsStaffOrOwner` is an object level permission, and `APIView` only runs
        # those for objects fetched through `get_object`, so it has to be checked
        # explicitly against the order.
        self.check_object_permissions(request, order)

        # Anything that is not pending is already settled: never call the payment
        # processor for it, otherwise opening the Order History page would re-run
        # handle_payment against every order the user ever placed.
        if order.status != ORDER.PENDING:
            return Response(self._serialize(order))

        return Response(self._serialize(self._resolve(request, order)))

    def _resolve(self, request, order):
        """
        Ask the payment processor whether the pending `order` has been paid, and
        fulfil it when it has.

        The outcome is reported to the monitoring under `RESOLUTION_ATTRIBUTE` as
        one of `confirmed`, `unconfirmed`, `payment-error`, `unexpected-error`,
        `paygate-not-installed` or `no-basket`. Only `confirmed` and `unconfirmed`
        are business as usual; the others are worth alerting on, as an order left
        pending by a bug looks exactly like one waiting for the user to pay.
        """
        # Imported lazily so that `nau_extensions` keeps working on a deployment
        # that does not install the PayGate plugin.
        try:
            from paygate.pending_orders import (  # pylint: disable=import-outside-toplevel
                confirm_pending_order, mark_order_as_payment_error)
            from paygate.processors import \
                PayGate  # pylint: disable=import-outside-toplevel
            from paygate.utils import \
                get_basket  # pylint: disable=import-outside-toplevel
        except ImportError:
            set_custom_attribute(RESOLUTION_ATTRIBUTE, "paygate-not-installed")
            logger.warning(
                "Cannot resolve the payment of order [%s]: the paygate plugin is not installed",
                order.number,
            )
            return order

        # `get_basket` assigns the strategy the basket needs to price its lines.
        basket = get_basket(order.basket_id, request)
        if basket is None:
            set_custom_attribute(RESOLUTION_ATTRIBUTE, "no-basket")
            logger.warning(
                "Cannot resolve the payment of order [%s]: it has no basket",
                order.number,
            )
            return order

        last_response = (
            PaymentProcessorResponse.objects
            .filter(basket=basket, processor_name=PayGate.NAME)
            .order_by("-created")
            .first()
        )

        try:
            order = confirm_pending_order(
                request,
                basket,
                order,
                last_response.response if last_response else {},
            )
            set_custom_attribute(RESOLUTION_ATTRIBUTE, "confirmed")
        except GatewayError:
            # Expected while a Multibanco reference has not been paid yet. The
            # order stays pending and the user can check again later.
            set_custom_attribute(RESOLUTION_ATTRIBUTE, "unconfirmed")
            logger.info(
                "Order [%s] is still not confirmed as payed by PayGate", order.number
            )
        except PaymentError:
            set_custom_attribute(RESOLUTION_ATTRIBUTE, "payment-error")
            logger.exception(
                "Payment error while resolving the payment of order [%s]", order.number
            )
            order = mark_order_as_payment_error(order)
        except Exception as exception:  # pylint: disable=broad-except
            # Never let an unexpected failure break the Order History page: the row
            # simply stays pending and can be resolved on the next visit. From the
            # outside such an order is indistinguishable from an unpaid Multibanco
            # reference, so it is reported apart to be alerted on: `unconfirmed` is
            # the normal course of business, `unexpected-error` never is.
            set_custom_attribute(RESOLUTION_ATTRIBUTE, "unexpected-error")
            set_custom_attribute(
                f"{RESOLUTION_ATTRIBUTE}_error", exception.__class__.__name__
            )
            logger.exception(
                "Unexpected error while resolving the payment of order [%s]",
                order.number,
            )

        return order

    @staticmethod
    def _serialize(order):
        return {
            "order_number": order.number,
            "status": order.status,
        }
