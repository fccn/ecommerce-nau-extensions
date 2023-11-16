from django.dispatch import receiver
from oscar.core.loading import get_class

from nau_extensions.models import BasketTransactionIntegration
from nau_extensions.tasks import send_basket_transaction_integration_to_financial_manager

post_checkout = get_class("checkout.signals", "post_checkout")


@receiver(
    post_checkout,
    dispatch_uid="create_and_send_basket_transaction_integration_to_financial_manager",
)
# @silence_exceptions("Failed to create and send basket transaction integration to financial manager.")
def create_and_send_basket_transaction_integration_to_financial_manager(
    sender, order=None, request=None, **kwargs
):  # pylint: disable=unused-argument
    """
    Create a Basket Transaction Integration object after a checkout of an Order;
    then send that information to the nau-financial-manager service.
    """
    BasketTransactionIntegration.create(order.basket).save()
    send_basket_transaction_integration_to_financial_manager.delay(order.basket)
