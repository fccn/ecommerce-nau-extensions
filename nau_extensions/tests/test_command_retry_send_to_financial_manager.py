from io import StringIO

import mock
from django.core.management import call_command
from django.test import TestCase
from nau_extensions.models import BasketTransactionIntegration

from ecommerce.extensions.test.factories import create_order
from ecommerce.tests.testcases import TestCase


@mock.patch(
    "nau_extensions.management.commands.retry_send_to_financial_manager.send_to_financial_manager_if_enabled"
)
class CommandsNAUExtensionsTests(TestCase):
    """
    This class aims to test the VAT customization required by NAU.
    """

    def _create_basket_transaction_integration(self, state=None):
        order = create_order()
        basket = order.basket
        bti = BasketTransactionIntegration.create(basket)
        if state:
            bti.state = state
        bti.save()
        return bti

    def test_retry_send_to_financial_manager_once(self, send_mock):
        """
        Test that retry sending a single BasketTransactionIntegration object to financial manager.
        """
        self._create_basket_transaction_integration(
            state=BasketTransactionIntegration.SENT_WITH_SUCCESS
        )
        bti_pending = self._create_basket_transaction_integration()

        call_command("retry_send_to_financial_manager", delta_to_be_sent_in_seconds=0)
        send_mock.assert_called_once_with(bti_pending)

    def test_retry_send_to_financial_manager_one_each_state(self, send_mock):
        """
        Test that retry sending with one BasketTransactionIntegration object per state
        to financial manager. The sent with success state shouldn't be sent.
        """
        bti_sent = self._create_basket_transaction_integration()
        bti_sent.state = BasketTransactionIntegration.SENT_WITH_SUCCESS
        bti_sent.save()

        bti_pending = self._create_basket_transaction_integration()
        bti_pending.state = BasketTransactionIntegration.TO_BE_SENT
        bti_pending.save()

        bti_error = self._create_basket_transaction_integration()
        bti_error.state = BasketTransactionIntegration.SENT_WITH_ERROR
        bti_error.save()

        call_command("retry_send_to_financial_manager", delta_to_be_sent_in_seconds=0)
        self.assertEqual(send_mock.call_count, 2)

    def test_retry_send_to_financial_manager_multiple(self, send_mock):
        """
        Test that retry sending multiple BasketTransactionIntegration object to financial manager.
        """
        for _ in range(10):
            self._create_basket_transaction_integration()
        call_command("retry_send_to_financial_manager", delta_to_be_sent_in_seconds=0)
        self.assertEqual(send_mock.call_count, 10)
