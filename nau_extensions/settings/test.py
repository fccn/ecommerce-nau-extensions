"""
Test settings for the ecommerce nau extensions
"""

from ecommerce.settings.test import *

INSTALLED_APPS += ("nau_extensions",)

# Mount the nau_extensions URLs the same way the deployment does, so the tests
# exercise the real paths. See `ECOMMERCE_EXTRA_PAYMENT_PROCESSOR_URLS` in
# nau-tutor-configs' config-fragment.yml, which produces `/payment/nau_extensions/`.
EXTRA_PAYMENT_PROCESSOR_URLS = {
    **EXTRA_PAYMENT_PROCESSOR_URLS,
    "nau_extensions": "nau_extensions.urls",
}

# This setting needs to be specified on this level.
NAU_EXTENSION_OSCAR_RATE_TAX_STRATEGY_CLASS = "nau_extensions.strategy.SettingFixedRateTax"
