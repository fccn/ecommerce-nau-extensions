from decimal import Decimal

import mock
import requests
from django.test import override_settings
from nau_extensions.financial_manager import (
    send_to_financial_manager_if_enabled, sync_request_data)
from nau_extensions.models import (BasketBillingInformation,
                                   BasketTransactionIntegration)
from nau_extensions.tests.factories import MockResponse, create_basket
from oscar.test.factories import CountryFactory

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.test.factories import create_order
from ecommerce.tests.factories import (PartnerFactory,
                                       SiteConfigurationFactory, SiteFactory,
                                       UserFactory)
from ecommerce.tests.testcases import TestCase


class FinancialManagerNAUExtensionsTests(TestCase):
    """
    This class aims to test the specifics of the nau extensions project related to the
    integration of financial manager.
    """

    # To view the full difference of the asserted dictionaries
    maxDiff = None

    @override_settings(OSCAR_DEFAULT_CURRENCY="EUR")
    def test_financial_manager_sync_data_basic(self):
        """
        Test the synchronization of data between the models and the `BasketTransactionIntegration`
        model.
        """
        partner = PartnerFactory(short_code="edX")
        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        honor_product = course.create_or_update_seat("honor", False, 0)
        verified_product = course.create_or_update_seat("verified", True, 10)

        owner = UserFactory(email="ecommerce@example.com")

        # create an empty basket so we know what it's inside
        basket = create_basket(owner=owner, empty=True)
        basket.add_product(verified_product)
        basket.add_product(honor_product)

        # creating an order will mark the card submitted
        create_order(basket=basket)

        bti = BasketTransactionIntegration.create(basket)

        basket.save()
        bti.save()

        country = CountryFactory(iso_3166_1_a2="PT", printable_name="Portugal")
        country.save()

        bbi = BasketBillingInformation()
        bbi.line1 = "Av. do Brasil n.º 101"
        bbi.line2 = "AA"
        bbi.line3 = "BB CC"
        bbi.line4 = "Lisboa"
        bbi.state = "Lisboa"
        bbi.postcode = "1700-066"
        bbi.country = country
        bbi.basket = basket
        bbi.vatin = "123456789"
        bbi.save()

        sync_request_data(bti)

        self.assertDictEqual(
            bti.request,
            {
                "transaction_id": basket.order_number,
                "transaction_type": "credit",
                "client_name": owner.full_name,
                "email": "ecommerce@example.com",
                "address_line_1": "Av. do Brasil n.º 101",
                "address_line_2": "AA, BB CC",
                "city": "Lisboa",
                "postal_code": "1700-066",
                "state": "Lisboa",
                "country_code": "PT",
                "vat_identification_number": "123456789",
                "vat_identification_country": "PT",
                "total_amount_exclude_vat": Decimal("10.00"),
                "total_amount_include_vat": Decimal("10.00"),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "amount_exclude_vat": Decimal("10.00"),
                        "amount_include_vat": Decimal("10.00"),
                        "description": "Seat in edX Demonstration Course with verified certificate",
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                        "vat_tax": Decimal("0.00"),
                    },
                    # honor
                    {
                        "amount_exclude_vat": Decimal("0.00"),
                        "amount_include_vat": Decimal("0.00"),
                        "description": "Seat in edX Demonstration Course with honor certificate",
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                        "vat_tax": Decimal("0.00"),
                    },
                ],
            },
        )

    @override_settings(
        NAU_EXTENSION_TAX_RATE="0.298701299",  # = 0.23/0.77,
        OSCAR_DEFAULT_CURRENCY="EUR"
    )
    def test_financial_manager_sync_data_with_tax_rate(self):
        """
        Test the synchronization of data between the models and the `BasketTransactionIntegration`
        model.
        """
        partner = PartnerFactory(short_code="edX")
        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        honor_product = course.create_or_update_seat("honor", False, 0)
        verified_product = course.create_or_update_seat("verified", True, 10)

        owner = UserFactory(email="ecommerce@example.com")

        # create an empty basket so we know what it's inside
        basket = create_basket(owner=owner, empty=True)
        basket.add_product(verified_product)
        basket.add_product(honor_product)

        # creating an order will mark the card submitted
        create_order(basket=basket)

        bti = BasketTransactionIntegration.create(basket)

        basket.save()
        bti.save()

        country = CountryFactory(iso_3166_1_a2="PT", printable_name="Portugal")
        country.save()

        bbi = BasketBillingInformation()
        bbi.line1 = "Av. do Brasil n.º 101"
        bbi.line2 = "AA"
        bbi.line3 = ""
        bbi.line4 = "Lisboa"
        bbi.state = "Lisboa"
        bbi.postcode = "1700-066"
        bbi.country = country
        bbi.basket = basket
        bbi.vatin = "123456789"
        bbi.save()

        sync_request_data(bti)

        self.assertDictEqual(
            bti.request,
            {
                "transaction_id": basket.order_number,
                "transaction_type": "credit",
                "client_name": owner.full_name,
                "email": "ecommerce@example.com",
                "address_line_1": "Av. do Brasil n.º 101",
                "address_line_2": "AA",
                "city": "Lisboa",
                "postal_code": "1700-066",
                "state": "Lisboa",
                "country_code": "PT",
                "vat_identification_number": "123456789",
                "vat_identification_country": "PT",
                "total_amount_exclude_vat": Decimal("10.00"),
                "total_amount_include_vat": Decimal("12.99"),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "amount_exclude_vat": Decimal("10.00"),
                        "amount_include_vat": Decimal("12.99"),
                        "description": "Seat in edX Demonstration Course with verified certificate",
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                        "vat_tax": Decimal("2.99"),
                    },
                    # honor
                    {
                        "amount_exclude_vat": Decimal("0.00"),
                        "amount_include_vat": Decimal("0.00"),
                        "description": "Seat in edX Demonstration Course with honor certificate",
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                        "vat_tax": Decimal("0.00"),
                    },
                ],
            },
        )

    @override_settings(OSCAR_DEFAULT_CURRENCY="EUR")
    def test_financial_manager_sync_data_without_bbi(self):
        """
        Test the synchronization of data between the models and the `BasketTransactionIntegration`
        model without a `BasketBillingInformation` object.
        """
        partner = PartnerFactory(short_code="edX")
        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        honor_product = course.create_or_update_seat("honor", False, 0)
        verified_product = course.create_or_update_seat("verified", True, 10)

        owner = UserFactory(email="ecommerce@example.com")

        # create an empty basket so we know what it's inside
        basket = create_basket(owner=owner, empty=True)
        basket.add_product(verified_product)
        basket.add_product(honor_product)

        # creating an order will mark the card submitted
        create_order(basket=basket)

        bti = BasketTransactionIntegration.create(basket)

        basket.save()
        bti.save()

        country = CountryFactory(iso_3166_1_a2="PT", printable_name="Portugal")
        country.save()

        sync_request_data(bti)

        self.assertDictEqual(
            bti.request,
            {
                "transaction_id": basket.order_number,
                "transaction_type": "credit",
                "client_name": owner.full_name,
                "email": "ecommerce@example.com",
                "address_line_1": None,
                "address_line_2": None,
                "city": None,
                "postal_code": None,
                "state": None,
                "country_code": None,
                "vat_identification_number": None,
                "vat_identification_country": None,
                "total_amount_exclude_vat": Decimal("10.00"),
                "total_amount_include_vat": Decimal("10.00"),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "amount_exclude_vat": Decimal("10.00"),
                        "amount_include_vat": Decimal("10.00"),
                        "description": "Seat in edX Demonstration Course with verified certificate",
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                        "vat_tax": Decimal("0.00"),
                    },
                    # honor
                    {
                        "amount_exclude_vat": Decimal("0.00"),
                        "amount_include_vat": Decimal("0.00"),
                        "description": "Seat in edX Demonstration Course with honor certificate",
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                        "vat_tax": Decimal("0.00"),
                    },
                ],
            },
        )

    @override_settings(
        NAU_FINANCIAL_MANAGER={
            "edx": {
                "url": "https://finacial-manager.example.com/api/billing/transaction-complete/",
                "token": "a-very-long-token",
            },
        },
    )
    def test_send_to_financial_manager(self):
        """
        Test that send to financial manager system.
        """
        partner = PartnerFactory(short_code="edX")

        site_configuration = SiteConfigurationFactory(partner=partner)
        site_configuration.site = SiteFactory(name="openedx")
        site = site_configuration.site

        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        honor_product = course.create_or_update_seat("honor", False, 0)
        verified_product = course.create_or_update_seat("verified", True, 10)

        owner = UserFactory(email="ecommerce@example.com")

        # create an empty basket so we know what it's inside
        basket = create_basket(owner=owner, empty=True, site=site)
        basket.add_product(verified_product)
        basket.add_product(honor_product)
        basket.save()

        # create billing information
        country = CountryFactory(iso_3166_1_a2="PT", printable_name="Portugal")
        country.save()
        bbi = BasketBillingInformation()
        bbi.line1 = "Av. do Brasil n.º 101"
        bbi.line2 = ""
        bbi.line3 = ""
        bbi.line4 = "Lisboa"
        bbi.state = "Lisboa"
        bbi.postcode = "1700-066"
        bbi.country = country
        bbi.basket = basket
        bbi.vatin = "123456789"
        bbi.save()

        # creating an order will mark the card submitted
        create_order(basket=basket)

        bti = BasketTransactionIntegration.create(basket)
        bti.save()

        mock_response_json_data = {
            "some": "stuff",
        }

        with mock.patch.object(
            requests,
            "post",
            return_value=MockResponse(
                json_data=mock_response_json_data,
                status_code=200,
            ),
        ):
            send_to_financial_manager_if_enabled(bti)

        self.assertEqual(bti.state, BasketTransactionIntegration.SENT_WITH_SUCCESS)
        self.assertEqual(mock_response_json_data, bti.response)

    @override_settings(
        NAU_FINANCIAL_MANAGER={
            "edx": {
                "url": "https://finacial-manager.example.com/api/billing/transaction-complete/",
                "token": "a-very-long-token",
            },
        },
    )
    def test_send_to_financial_manager_without_basket_billing_information(self):
        """
        Test that send to financial manager system.
        """
        partner = PartnerFactory(short_code="edX")

        site_configuration = SiteConfigurationFactory(partner=partner)
        site_configuration.site = SiteFactory(name="openedx")
        site = site_configuration.site

        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        honor_product = course.create_or_update_seat("honor", False, 0)
        verified_product = course.create_or_update_seat("verified", True, 10)

        owner = UserFactory(email="ecommerce@example.com")

        # create an empty basket so we know what it's inside
        basket = create_basket(owner=owner, empty=True, site=site)
        basket.add_product(verified_product)
        basket.add_product(honor_product)
        basket.save()

        # creating an order will mark the card submitted
        create_order(basket=basket)

        bti = BasketTransactionIntegration.create(basket)
        bti.save()

        mock_response_json_data = {
            "some": "stuff",
        }

        with mock.patch.object(
            requests,
            "post",
            return_value=MockResponse(
                json_data=mock_response_json_data,
                status_code=200,
            ),
        ):
            send_to_financial_manager_if_enabled(bti)

        self.assertEqual(bti.state, BasketTransactionIntegration.SENT_WITH_SUCCESS)
        self.assertEqual(mock_response_json_data, bti.response)