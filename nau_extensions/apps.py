"""
NAU extensions of Open edX ecommerce.
"""
from django.apps import AppConfig
from django.conf.urls import url

from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class NauExtensionsConfig(AppConfig): # OscarConfig
    """
    NAU Extensions for the Open edX Ecommerce.
    """
    name = 'nau_extensions'
    verbose_name = 'Django Ecommerce plugin with NAU custom extensions app.'
    plugin_app = {
        'url_config': {
            'ecommerce': {
                'namespace': 'nau',
            }
        },
    }

    def ready(self):
        print("Nau extensions loading...")
