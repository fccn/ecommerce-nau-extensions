"""
Test settings for the ecommerce nau extensions
"""

from ecommerce.settings.test import *

INSTALLED_APPS += ("nau_extensions",)

# This setting needs to be specified on this level.
NAU_EXTENSION_OSCAR_RATE_TAX_STRATEGY_CLASS = "nau_extensions.strategy.SettingFixedRateTax"
