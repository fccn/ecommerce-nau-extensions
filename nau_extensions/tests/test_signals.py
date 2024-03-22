
import mock
from nau_extensions.models import BasketTransactionIntegration

from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.test.factories import create_order
from ecommerce.tests.factories import UserFactory
from ecommerce.tests.testcases import TestCase


class SignalsNAUExtensionsTests(TestCase):
    """
    This class aims to test the specifics of the nau extensions project related to django models.
    """

    def test_signal_receiver_create_and_send_basket_transaction_integration_to_financial_manager(self):
        """
        Test that after a checkout the `create_and_send_basket_transaction_integration_to_financial_manager`
        is trigged.
        """
        order = create_order(user=UserFactory())
        EdxOrderPlacementMixin().handle_successful_order(order)
        bti = BasketTransactionIntegration.get_by_basket(order.basket)
        self.assertTrue(bti is not None)
