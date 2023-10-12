from celery import shared_task

from .models import BasketTransactionIntegration

@shared_task(bind=True, ignore_result=True)
def send_basket_transaction_integration_to_financial_manager(self, basket):
    """
    Send Basket Transaction Integration to the nau-financial-manager service.

    Args:
        self: Ignore
        basket (Basket): the basket to send
    """
    basket.basket_transaction_integration.send_to_financial_manager()
