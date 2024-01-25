from nau_extensions.vatin import check_country_vatin

from ecommerce.tests.testcases import TestCase


class VATINNAUExtensionsTests(TestCase):
    """
    This class aims to test the VAT customization required by NAU.
    """

    def test_vatin_pt_fake(self):
        """
        Test the VATIN validator for a fake VAT identification number in Portugal.
        """
        self.assertEqual(True, check_country_vatin("PT", "123456789"))

    def test_vatin_pt_fct(self):
        """
        Test the VATIN validator for a real VAT identification number in Portugal.
        """
        self.assertEqual(True, check_country_vatin("PT", "600021505"))

    def test_vatin_fr(self):
        """
        Test the VATIN validator for a fake VAT identification number in France.
        """
        self.assertEqual(True, check_country_vatin("FR", "12345678901"))

    def test_vatin_es(self):
        """
        Test the VATIN validator for a fake VAT identification number in Spain.
        """
        self.assertEqual(True, check_country_vatin("ES", "B34562534"))

    def test_vatin_de(self):
        """
        Test the VATIN validator for a fake VAT identification number in Germany.
        """
        self.assertEqual(True, check_country_vatin("DE", "123456789"))
