"""
Django Oscar strategy for fixed rate tax.
Use a fixed rate tax read from a setting.
"""

from decimal import Decimal as D

from django.conf import settings
from oscar.apps.partner import strategy


class SettingFixedRateTax(strategy.FixedRateTax):
    """
    A custom rate tax that loads a fixed value from a setting.
    This means that everything we sell has a fixed VAT value.
    """

    def get_rate(self, product, stockrecord):
        """
        The rate VAT that all products have.
        """
        return D(settings.NAU_EXTENSION_TAX_RATE)
