"""
Test settings for the ecommerce nau extensions
"""

from social_core.pipeline import DEFAULT_AUTH_PIPELINE

from ecommerce.settings.test import *

INSTALLED_APPS += ("nau_extensions",)

# This setting needs to be specified on this level.
NAU_EXTENSION_OSCAR_RATE_TAX_STRATEGY_CLASS = "nau_extensions.strategy.SettingFixedRateTax"

# Mirror the deployment pipeline, see `ecommerce_config.py` in nau-tutor-configs.
_create_user_index = DEFAULT_AUTH_PIPELINE.index("social_core.pipeline.user.create_user")
SOCIAL_AUTH_PIPELINE = (
    DEFAULT_AUTH_PIPELINE[:_create_user_index]
    + ("nau_extensions.pipeline.truncate_user_details",)
    + DEFAULT_AUTH_PIPELINE[_create_user_index:]
)
