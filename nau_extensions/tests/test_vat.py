from decimal import Decimal

from django.test import override_settings
from nau_extensions.tests.factories import create_basket

from ecommerce.extensions.partner.strategy import DefaultStrategy
from ecommerce.tests.testcases import TestCase


@override_settings(
    NAU_EXTENSION_TAX_RATE="0.298701299",  # = 0.23/0.77
)
class VATNAUExtensionsTests(TestCase):
    """
    This class aims to test the VAT customization required by NAU.
    """

    def test_vat_tax(self):
        """
        Test that the VAT tax extension is applied on Django Oscar strategy.
        """
        self.assertEqual(DefaultStrategy().get_rate(None, None), Decimal("0.298701299"))

    def test_basket_with_vat_tax(self):
        """
        Test that VAT tax value is applied on a basket.
        """
        basket = create_basket(price="15.40")
        self.assertEqual(basket.total_excl_tax, round(Decimal(15.40), 2))
        self.assertEqual(basket.total_incl_tax, round(Decimal(20.00), 2))
