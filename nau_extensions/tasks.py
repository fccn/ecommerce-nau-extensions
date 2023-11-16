from celery import shared_task

from .financial_manager import send_to_financial_manager_if_enabled


@shared_task(bind=True, ignore_result=True)
def send_basket_transaction_integration_to_financial_manager(self, basket):  # pylint: disable=unused-argument
    """
    Send Basket Transaction Integration to the nau-financial-manager service.

    Args:
        self: Ignore
        basket (Basket): the basket to send
    """
    send_to_financial_manager_if_enabled(basket.basket_transaction_integration)
