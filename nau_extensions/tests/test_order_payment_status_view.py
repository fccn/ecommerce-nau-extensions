"""
Tests for the `OrderPaymentStatusView`, the endpoint that lazily resolves the
payment of an order created by an asynchronous payment method.

On NAU the relevant asynchronous method is the Multibanco reference (`REFMB`):
PayGate hands the learner a reference that can be paid days later. The order is
placed in the `Pending` status when the learner returns from PayGate, and this
endpoint -- called by the Order History page, once per pending row -- is what
turns it into a paid, fulfilled order.
"""

from decimal import Decimal

import mock
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from oscar.apps.payment.exceptions import GatewayError, PaymentError
from oscar.core.loading import get_model
from paygate.pending_orders import place_pending_order
from paygate.processors import PayGate

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.fulfillment.status import ORDER
from ecommerce.extensions.payment.processors import HandledProcessorResponse
from ecommerce.extensions.test.factories import create_basket
from ecommerce.tests.testcases import TestCase

Order = get_model("order", "Order")

PAYGATE_CONFIG = {
    "edx": {
        **settings.PAYMENT_PROCESSOR_CONFIG["edx"],
        **{
            "paygate": {
                "access_token": "PwdX_XXXX_YYYY",
                "merchant_code": "NAU",
                "api_checkout_url": "https://test.optimistic.blue/paygateWS/api/CheckOut",
                "api_back_search_transactions": (
                    "https://test.optimistic.blue/paygateWS/api/BackOfficeSearchTransactions"
                ),
                "api_basic_auth_user": "NAU",
                "api_basic_auth_pass": "APassword",
            }
        },
    }
}


def handled_response(transaction_id="MB-TXN-1", total="20.00"):
    return HandledProcessorResponse(
        transaction_id=transaction_id,
        total=Decimal(total),
        currency="EUR",
        card_number="REFMB",
        card_type="REFMB",
    )


@override_settings(PAYMENT_PROCESSOR_CONFIG=PAYGATE_CONFIG)
class OrderPaymentStatusViewTests(TestCase):
    """
    Tests for GET /payment/nau_extensions/order-payment-status/
    """

    def setUp(self):
        super().setUp()
        # `create_user` (from UserMixin) sets a password we can log in with.
        self.user = self.create_user()
        self.url = reverse("ecommerce_nau_extensions:order_payment_status")

    def create_pending_order(self, owner=None):
        course = CourseFactory(id="a/b/c", name="Demo Course", partner=self.partner)
        product = course.create_or_update_seat("test-certificate-type", False, 20)
        basket = create_basket(site=self.site, owner=owner or self.user, empty=True)
        basket.add_product(product)
        basket.save()
        self.request.user = basket.owner
        return place_pending_order(self.request, basket)

    def get(self, order_number):
        return self.client.get(self.url, {"order_number": order_number})

    def test_requires_authentication(self):
        response = self.get("OPENEDX-100001")
        self.assertIn(response.status_code, (401, 403))

    def test_missing_order_number_is_not_found(self):
        self.client.login(username=self.user.username, password=self.password)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_unknown_order_is_not_found(self):
        self.client.login(username=self.user.username, password=self.password)
        self.assertEqual(self.get("DOES-NOT-EXIST").status_code, 404)

    def test_another_user_cannot_read_the_status_of_my_order(self):
        order = self.create_pending_order()
        other = self.create_user()
        self.client.login(username=other.username, password=self.password)

        self.assertEqual(self.get(order.number).status_code, 403)

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_a_settled_order_never_calls_the_payment_processor(
        self, mock_handle_processor_response,
    ):
        """
        The Order History page shows every order the learner ever placed. Asking
        PayGate about the ones that are already paid would re-run `handle_payment`
        against them on every page load.
        """
        order = self.create_pending_order()
        order.set_status(ORDER.OPEN)
        order.set_status(ORDER.COMPLETE)
        self.client.login(username=self.user.username, password=self.password)

        response = self.get(order.number)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], ORDER.COMPLETE)
        mock_handle_processor_response.assert_not_called()

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_a_pending_order_stays_pending_while_the_reference_is_unpaid(
        self, mock_handle_processor_response,
    ):
        """
        An unpaid Multibanco reference makes PayGate raise a GatewayError. That is
        the expected outcome, not an error: the order stays pending and the learner
        can check again later.
        """
        mock_handle_processor_response.side_effect = GatewayError(
            "PayGate couldn't double check if basket has been payed"
        )
        order = self.create_pending_order()
        self.client.login(username=self.user.username, password=self.password)

        response = self.get(order.number)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], ORDER.PENDING)
        order.refresh_from_db()
        self.assertEqual(order.status, ORDER.PENDING)
        self.assertEqual(order.sources.count(), 0)

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_a_paid_reference_settles_and_fulfils_the_order(
        self, mock_handle_processor_response,
    ):
        """
        The core of the feature: opening the Order History page after paying the
        reference records the payment and fulfils the order.
        """
        mock_handle_processor_response.return_value = handled_response()
        order = self.create_pending_order()
        self.client.login(username=self.user.username, password=self.password)

        response = self.get(order.number)

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["status"], ORDER.PENDING)

        order.refresh_from_db()
        self.assertNotEqual(order.status, ORDER.PENDING)
        self.assertEqual(order.sources.count(), 1)
        self.assertEqual(order.payment_events.count(), 1)
        self.assertEqual(order.sources.first().reference, "MB-TXN-1")
        self.assertEqual(order.sources.first().amount_debited, Decimal("20.00"))

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_resolving_twice_does_not_record_the_payment_twice(
        self, mock_handle_processor_response,
    ):
        """
        The learner may open the Order History page repeatedly. Once the order is
        settled the endpoint must short-circuit.
        """
        mock_handle_processor_response.return_value = handled_response()
        order = self.create_pending_order()
        self.client.login(username=self.user.username, password=self.password)

        self.get(order.number)
        self.get(order.number)

        order.refresh_from_db()
        self.assertEqual(order.sources.count(), 1)
        self.assertEqual(order.payment_events.count(), 1)
        self.assertEqual(mock_handle_processor_response.call_count, 1)

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_a_payment_error_marks_the_order_as_such(
        self, mock_handle_processor_response,
    ):
        mock_handle_processor_response.side_effect = PaymentError("card declined")
        order = self.create_pending_order()
        self.client.login(username=self.user.username, password=self.password)

        response = self.get(order.number)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], ORDER.PAYMENT_ERROR)
        order.refresh_from_db()
        self.assertEqual(order.status, ORDER.PAYMENT_ERROR)
        self.assertEqual(order.sources.count(), 0)

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_an_unexpected_error_leaves_the_order_pending(
        self, mock_handle_processor_response,
    ):
        """
        The Order History page must keep working even if resolving one row blows up
        in a way we did not anticipate. The row simply stays pending.
        """
        mock_handle_processor_response.side_effect = ValueError("boom")
        order = self.create_pending_order()
        self.client.login(username=self.user.username, password=self.password)

        response = self.get(order.number)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], ORDER.PENDING)
        order.refresh_from_db()
        self.assertEqual(order.status, ORDER.PENDING)

    @mock.patch.object(PayGate, "handle_processor_response")
    def test_staff_can_read_the_status_of_any_order(
        self, mock_handle_processor_response,
    ):
        mock_handle_processor_response.side_effect = GatewayError("not payed yet")
        order = self.create_pending_order()
        staff = self.create_user(is_staff=True)
        self.client.login(username=staff.username, password=self.password)

        response = self.get(order.number)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["order_number"], order.number)
