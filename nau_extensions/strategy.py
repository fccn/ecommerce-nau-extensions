"""
Django Oscar strategy for fixed rate tax.
Use a fixed rate tax read from a setting.
"""
from decimal import Decimal as D

from django.conf import settings
from oscar.apps.partner import strategy

from ecommerce.extensions.partner.strategy import \
    CourseSeatAvailabilityPolicyMixin


class DefaultStrategy(
    strategy.UseFirstStockRecord,
    CourseSeatAvailabilityPolicyMixin,
    strategy.FixedRateTax,
    strategy.Structured,
):
    def get_rate(self, product, stockrecord):
        return D(settings.NAU_EXTENSION_TAX_RATE)
