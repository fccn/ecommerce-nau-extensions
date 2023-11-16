"""
Service layer of the integration with nau-financial-manager service.
"""
import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from opaque_keys.edx.keys import CourseKey
from oscar.core.loading import get_class, get_model

from .models import BasketTransactionIntegration
from .utils import get_order

logger = logging.getLogger(__name__)
Selector = get_class("partner.strategy", "Selector")
Order = get_model("order", "Order")


def is_financial_manager_enabled(site) -> bool:
    """
    Check if there is a valid `NAU_FINANCIAL_MANAGER` setting for the `site`.
    """
    partner_short_code = site.siteconfiguration.partner.short_code
    enabled = hasattr(settings, "NAU_FINANCIAL_MANAGER") and (
        partner_short_code.lower() in settings.NAU_FINANCIAL_MANAGER
    )
    if not enabled:
        logger.info(
            "Missing `NAU_FINANCIAL_MANAGER` setting for partner `%s`",
            partner_short_code.lower(),
        )
    return enabled


def _get_financial_manager_setting(site, key, default=None):
    partner_short_code = site.siteconfiguration.partner.short_code
    if not default and key not in settings.NAU_FINANCIAL_MANAGER[partner_short_code.lower()]:
        msg = f"Missing setting `NAU_FINANCIAL_MANAGER['{partner_short_code.lower()}']['{key}']`"
        logger.warning(msg)
        raise ImproperlyConfigured(msg)
    return settings.NAU_FINANCIAL_MANAGER[partner_short_code.lower()].get(key, default)


def sync_request_data(bti: BasketTransactionIntegration) -> dict:
    """
    Synchronize the basket information with this BasketTransactionIntegration instance
    `request` field.
    """
    # initialize strategy
    basket = bti.basket
    basket.strategy = Selector().strategy(user=basket.owner)
    bbi = basket.basket_billing_information

    address_line_2 = bbi.line2 + (
        ("," + bbi.line3) if bbi.line3 and len(bbi.line3) > 0 else ""
    )
    order = get_order(basket)

    # generate a dict with all request data
    request_data = {
        "transaction_id": basket.order_number,
        "transaction_type": "credit",
        "client_name": basket.owner.full_name,
        "email": basket.owner.email,
        "address_line_1": bbi.line1,
        "address_line_2": address_line_2,
        "city": bbi.line4,
        "postal_code": bbi.postcode,
        "state": bbi.state,
        "country_code": bbi.country.iso_3166_1_a2,
        "vat_identification_number": bbi.vatin,
        "vat_identification_country": bbi.country.iso_3166_1_a2,
        "total_amount_exclude_vat": basket.total_excl_tax,
        "total_amount_include_vat": basket.total_incl_tax,
        "currency": basket.currency,
        "payment_type": _get_payment_type(order),
        "items": _convert_order_lines(order),
    }

    # update the request that will be sent to nau-financial-manager
    bti.request = request_data
    bti.save()

    # return also the data
    return request_data


def _get_payment_type(order):
    source = order.sources.first()
    if source:
        if source.card_type:
            return source.card_type
    return None


def _convert_order_lines(order):
    """
    Convert the Ecommerce order lines to the nau-financial-manager format.
    """
    result = []
    for line in order.lines.all():
        # line.discount_incl_tax
        # line.discount_excl_tax
        course_run_key = CourseKey.from_string(line.product.course.id)
        result.append(
            {
                "description": line.title,
                "quantity": line.quantity,
                "vat_tax": 1 - (line.unit_price_excl_tax - line.unit_price_incl_tax),
                "amount_exclude_vat": line.quantity * line.unit_price_excl_tax,
                "amount_include_vat": line.quantity * line.unit_price_incl_tax,
                "organization_code": course_run_key.org,
                "product_code": course_run_key.course,
                "product_id": line.product.course.id,
            }
        )
    return result


def send_to_financial_manager_if_enabled(
    basket_transaction_integration: BasketTransactionIntegration,
):
    """
    The service that calls the nau-financial-manager with the request data pre saved on the
    `BasketTransactionIntegration` instance, then save the response data.
    """
    site = basket_transaction_integration.basket.site
    if is_financial_manager_enabled(site):
        sync_request_data(basket_transaction_integration)
        url = _get_financial_manager_setting(site, "url")
        token = _get_financial_manager_setting(site, "token")
        response = requests.post(
            url,
            json=basket_transaction_integration.request,
            headers={"Authorization": token},
            timeout=30,
        )

        # update state
        if basket_transaction_integration.status_code == 200:
            state = BasketTransactionIntegration.SENT_WITH_SUCCESS
        else:
            state = BasketTransactionIntegration.SENT_WITH_ERROR
        basket_transaction_integration.state = state

        # save the response output
        basket_transaction_integration.response = response.content

        basket_transaction_integration.save()
