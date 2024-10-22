from decimal import Decimal

import mock
import requests
from django.test import override_settings
from nau_extensions.financial_manager import (
    get_receipt_link, send_to_financial_manager_if_enabled, sync_request_data)
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

        owner = UserFactory(email="ecommerce@example.com", full_name="Jon Snow")

        # create an empty basket so we know what it's inside
        basket = create_basket(owner=owner, empty=True)
        basket.add_product(verified_product, quantity=3)
        basket.add_product(honor_product, quantity=2)

        # creating an order will mark the card submitted
        create_order(basket=basket)

        bti = BasketTransactionIntegration.create(basket)

        basket.save()
        bti.save()

        country = CountryFactory(iso_3166_1_a2="PT", printable_name="Portugal")
        country.save()

        bbi = BasketBillingInformation()
        bbi.first_name = "Fundação"
        bbi.last_name = "Ciência Tecnologia"
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
                "client_name": "Fundação Ciência Tecnologia",
                "email": "ecommerce@example.com",
                "address_line_1": "Av. do Brasil n.º 101",
                "address_line_2": "AA, BB CC",
                "city": "Lisboa",
                "postal_code": "1700-066",
                "state": "Lisboa",
                "country_code": "PT",
                "vat_identification_number": "123456789",
                "vat_identification_country": "PT",
                "total_amount_include_vat": Decimal("30.00"),
                "total_discount_incl_tax": Decimal('0.00'),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "unit_price_incl_vat": Decimal("10.00"),
                        "description": "Lugar em edX Demonstration Course com certificado pago",
                        'discount_excl_tax': Decimal('0.00'),
                        'discount_incl_tax': Decimal('0.00'),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 3,
                    },
                    # honor
                    {
                        "unit_price_incl_vat": Decimal("0.00"),
                        "description": "Lugar em edX Demonstration Course com certificado grátis",
                        'discount_excl_tax': Decimal('0.00'),
                        'discount_incl_tax': Decimal('0.00'),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 2,
                    },
                ],
            },
        )

    @override_settings(OSCAR_DEFAULT_CURRENCY="EUR")
    def test_financial_manager_sync_data_with_quantity(self):
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

        owner = UserFactory(email="ecommerce@example.com", full_name="Jon Snow")

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
        bbi.first_name = "Fundação"
        bbi.last_name = "Ciência Tecnologia"
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
                "client_name": "Fundação Ciência Tecnologia",
                "email": "ecommerce@example.com",
                "address_line_1": "Av. do Brasil n.º 101",
                "address_line_2": "AA, BB CC",
                "city": "Lisboa",
                "postal_code": "1700-066",
                "state": "Lisboa",
                "country_code": "PT",
                "vat_identification_number": "123456789",
                "vat_identification_country": "PT",
                "total_amount_include_vat": Decimal("10.00"),
                "total_discount_incl_tax": Decimal('0.00'),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "unit_price_incl_vat": Decimal("10.00"),
                        "description": "Lugar em edX Demonstration Course com certificado pago",
                        'discount_excl_tax': Decimal('0.00'),
                        'discount_incl_tax': Decimal('0.00'),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                    },
                    # honor
                    {
                        "unit_price_incl_vat": Decimal("0.00"),
                        "description": "Lugar em edX Demonstration Course com certificado grátis",
                        'discount_excl_tax': Decimal('0.00'),
                        'discount_incl_tax': Decimal('0.00'),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                    },
                ],
            },
        )

    @override_settings(
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

        owner = UserFactory(email="ecommerce@example.com", full_name="Jon Snow")

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
                "client_name": "Jon Snow",
                "email": "ecommerce@example.com",
                "address_line_1": "Av. do Brasil n.º 101",
                "address_line_2": "AA",
                "city": "Lisboa",
                "postal_code": "1700-066",
                "state": "Lisboa",
                "country_code": "PT",
                "vat_identification_number": "123456789",
                "vat_identification_country": "PT",
                "total_amount_include_vat": Decimal("10.00"),
                "total_discount_incl_tax": Decimal('0.00'),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "unit_price_incl_vat": Decimal("10.00"),
                        "description": "Lugar em edX Demonstration Course com certificado pago",
                        'discount_excl_tax': Decimal('0.00'),
                        'discount_incl_tax': Decimal('0.00'),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                    },
                    # honor
                    {
                        "unit_price_incl_vat": Decimal("0.00"),
                        "description": "Lugar em edX Demonstration Course com certificado grátis",
                        'discount_excl_tax': Decimal('0.00'),
                        'discount_incl_tax': Decimal('0.00'),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
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
                "total_amount_include_vat": Decimal("10.00"),
                "total_discount_incl_tax": Decimal("0.00"),
                "currency": "EUR",
                "payment_type": None,
                "items": [
                    # verified
                    {
                        "unit_price_incl_vat": Decimal("10.00"),
                        "description": "Lugar em edX Demonstration Course com certificado pago",
                        "discount_excl_tax": Decimal("0.00"),
                        "discount_incl_tax": Decimal("0.00"),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
                    },
                    # honor
                    {
                        "unit_price_incl_vat": Decimal("0.00"),
                        "description": "Lugar em edX Demonstration Course com certificado grátis",
                        "discount_excl_tax": Decimal("0.00"),
                        "discount_incl_tax": Decimal("0.00"),
                        "organization_code": "edX",
                        "product_code": "DemoX",
                        "product_id": "course-v1:edX+DemoX+Demo_Course",
                        "quantity": 1,
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
                status_code=201,
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
                status_code=201,
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
    def test_send_to_financial_manager_duplicate_transaction(self):
        """
        Test that sends transaction to financial manager system with an already sent transaction.
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
            "transaction_id": [
                "transaction with this transaction id already exists."
            ],
        }

        with mock.patch.object(
            requests,
            "post",
            return_value=MockResponse(
                json_data=mock_response_json_data,
                status_code=400,
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
    def test_send_to_financial_manager_other_error(self):
        """
        Test that sends a transaction to financial manager system, but receives an unexpected error.
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
            "other_field": [
                "Some error."
            ],
        }

        with mock.patch.object(
            requests,
            "post",
            return_value=MockResponse(
                json_data=mock_response_json_data,
                status_code=400,
            ),
        ):
            send_to_financial_manager_if_enabled(bti)

        self.assertEqual(bti.state, BasketTransactionIntegration.SENT_WITH_ERROR)
        self.assertEqual(mock_response_json_data, bti.response)

    @override_settings(
        NAU_FINANCIAL_MANAGER={
            "edx": {
                "receipt-link-url": "https://finacial-manager.example.com/api/billing/receipt-link/",
                "token": "a-very-long-token",
            },
        },
    )
    @mock.patch.object(requests, "get", return_value=MockResponse(
        json_data="https://example.com/somereceipt.pdf",
        status_code=200,
    ))
    def test_get_receipt_link_found(self, mock_fm_receipt_link):
        """
        Test the `get_receipt_link` method.
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
        order = create_order(basket=basket)

        link = get_receipt_link(order)
        mock_fm_receipt_link.assert_called_once_with(f"https://finacial-manager.example.com/api/billing/receipt-link/{basket.order_number}/", headers={'Authorization': 'a-very-long-token'}, timeout=10)

        self.assertEqual(link, "https://example.com/somereceipt.pdf")

    @override_settings(
        NAU_FINANCIAL_MANAGER={
            "edx": {
                "receipt-link-url": "https://finacial-manager.example.com/api/billing/receipt-link/",
                "token": "a-very-long-token",
            },
        },
    )
    @mock.patch.object(requests, "get", return_value=MockResponse(
        status_code=404,
    ))
    def test_get_receipt_link_not_found(self, mock_fm_receipt_link):
        """
        Test the `get_receipt_link` method.
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
        order = create_order(basket=basket)

        link = get_receipt_link(order)
        mock_fm_receipt_link.assert_called_once_with(f"https://finacial-manager.example.com/api/billing/receipt-link/{basket.order_number}/", headers={'Authorization': 'a-very-long-token'}, timeout=10)

        self.assertEqual(link, None)
