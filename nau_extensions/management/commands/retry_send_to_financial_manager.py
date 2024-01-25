"""
Script to synchronize courses to Richie marketing site
"""

import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from nau_extensions.financial_manager import \
    send_to_financial_manager_if_enabled
from nau_extensions.models import BasketTransactionIntegration
from oscar.core.loading import get_model

Basket = get_model("basket", "Basket")


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command that retries to send the BasketTransactionIntegration objects to
    the Financial Manager system.
    By default, will retry the BasketTransactionIntegration objects where its state is sent with
    error and also send the pending to be sent that have been created more than 5 minutes ago.
    """

    help = (
        "Retry send the BasketTransactionIntegration objects to the "
        "Financial Manager system that have been sent with error or that "
        "haven't being sent on the last 5 minutes"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--basket_id",
            type=str,
            default=None,
            help="Basket id to synchronize, otherwise all pending baskets will be sent",
        )
        parser.add_argument(
            "--delta_to_be_sent_in_seconds",
            type=int,
            default=300,
            help="Delta in seconds to retry the To be sent state",
        )

    def handle(self, *args, **kwargs):
        """
        Synchronize courses to the Richie marketing site, print to console its sync progress.
        """
        btis: list = None

        basket_id = kwargs["basket_id"]
        if basket_id:
            basket = Basket.objects.filter(id=basket_id)
            if not basket:
                raise ValueError(f"No basket found for basket_id={basket_id}")
            bti = BasketTransactionIntegration.get_by_basket(basket)
            if not bti:
                raise ValueError(
                    f"No basket transaction integration found for basket_id={basket_id}"
                )
            btis = [bti]
        else:
            btis = BasketTransactionIntegration.objects.filter(
                state__in=[
                    BasketTransactionIntegration.SENT_WITH_ERROR,
                    BasketTransactionIntegration.TO_BE_SENT,
                ]
            )

        delta_to_be_sent_in_seconds = kwargs["delta_to_be_sent_in_seconds"]
        for bti in btis:
            if bti.created <= datetime.now(bti.created.tzinfo) - timedelta(
                seconds=delta_to_be_sent_in_seconds
            ):
                log.info("Sending to financial manager basket_id=%d", bti.basket.id)
                send_to_financial_manager_if_enabled(bti)
