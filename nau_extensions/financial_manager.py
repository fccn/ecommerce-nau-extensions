"""
Service layer of the integration with nau-financial-manager service.
"""
import logging

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from nau_extensions.models import (BasketBillingInformation,
                                   BasketTransactionIntegration)
from nau_extensions.utils import get_order
from opaque_keys.edx.keys import CourseKey
from oscar.core.loading import get_class, get_model

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
    bbi = BasketBillingInformation.get_by_basket(basket)
    order = get_order(basket)

    client_name = ' '.join(filter(None, [getattr(bbi, "first_name", None), getattr(bbi, "last_name", None)]))
    # fall back to the requested user full name, received from LMS.
    if not client_name:
        client_name = basket.owner.full_name
    address_line_1 = getattr(bbi, "line1", None)
    line2 = getattr(bbi, "line2", None)
    line3 = getattr(bbi, "line3", None)
    address_line_2 = ", ".join(filter(None, [line2, line3]))
    address_line_2 = address_line_2 if address_line_2 else None
    city = getattr(bbi, "line4", None)
    postal_code = getattr(bbi, "postcode", None)
    state = getattr(bbi, "state", None)
    country_code = bbi.country.iso_3166_1_a2 if bbi else None
    vat_identification_number = bbi.vatin if bbi else None
    vat_identification_country = bbi.country.iso_3166_1_a2 if bbi else None

    # generate a dict with all request data
    request_data = {
        "transaction_id": basket.order_number,
        "transaction_type": "credit",
        "client_name": client_name,
        "email": basket.owner.email,
        "address_line_1": address_line_1,
        "address_line_2": address_line_2,
        "city": city,
        "postal_code": postal_code,
        "state": state,
        "country_code": country_code,
        "vat_identification_number": vat_identification_number,
        "vat_identification_country": vat_identification_country,
        "total_amount_include_vat": order.total_incl_tax,
        "total_discount_incl_tax": order.total_discount_incl_tax,
        "currency": order.currency,
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
        course = line.product.course
        course_id = course.id if course else line.product.title
        course_key = CourseKey.from_string(course.id) if course else None
        organization_code = course_key.org if course else None
        product_code = course_key.course if course else None
        unit_price_incl_tax = line.unit_price_incl_tax
        result.append(
            {
                "description": line.title,
                "quantity": line.quantity,
                "unit_price_incl_vat": unit_price_incl_tax,
                "organization_code": organization_code,
                "product_code": product_code,
                "product_id": course_id,
                "discount_excl_tax": line.discount_excl_tax,
                "discount_incl_tax": line.discount_incl_tax,
            }
        )
    return result


def send_to_financial_manager_if_enabled(
    basket_transaction_integration: BasketTransactionIntegration,
) -> bool:
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

        # Convert response to json
        try:
            response_json = response.json()
        except Exception as e:  # pylint: disable=broad-except
            response_json = None
            logger.exception("Error can't parse send to financial manager response as json [%s]", e)

        # update state
        state = BasketTransactionIntegration.SENT_WITH_ERROR
        if response.status_code == 201:
            state = BasketTransactionIntegration.SENT_WITH_SUCCESS

        # is duplicate
        if response.status_code == 400:
            transaction_id_error = response_json.get("transaction_id", [])
            if len(transaction_id_error) > 0 \
                    and transaction_id_error[0] == "transaction with this transaction id already exists.":
                state = BasketTransactionIntegration.SENT_WITH_SUCCESS

        basket_transaction_integration.state = state

        # save the response output

        basket_transaction_integration.response = response_json
        basket_transaction_integration.save()
        return True
    return False


def get_receipt_link(order):
    """
    Get the Receipt Link from NAU Financial Manager, this will transform the order_number to the receipt link.
    """
    site = order.basket.site
    if is_financial_manager_enabled(site):
        transaction_id = order.basket.order_number
        receipt_link_url = _get_financial_manager_setting(site, "receipt-link-url")
        if not receipt_link_url.endswith('/'):
            receipt_link_url += '/'
        receipt_link_url += transaction_id + '/'
        token = _get_financial_manager_setting(site, "token")
        response = None
        try:
            logger.info("Get receipt link for transaction id [%s]", transaction_id)
            response = requests.get(
                receipt_link_url,
                headers={"Authorization": token},
                timeout=10,
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Error can't get receipt link for transaction_id [%s] error: [%s]", transaction_id, e)
            return None
        finally:
            logger.info("Received the receipt link status_code: [%d]", response.status_code if response else None)
        if response.status_code == 200:
            logger.info("Received the receipt link content: [%s]", response.content)
            return response.content
    return None
