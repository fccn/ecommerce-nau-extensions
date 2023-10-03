"""
NAU extensions of Open edX ecommerce.
"""
from django.apps import AppConfig


class NauExtensionsConfig(AppConfig):
    """
    NAU Extensions for the Open edX Ecommerce.
    """

    name = "nau_extensions"
    verbose_name = "Django Ecommerce plugin with NAU custom extensions app."
    plugin_app = {
        "url_config": {
            "ecommerce": {
                "namespace": "nau",
            }
        },
    }

    def ready(self):
        print("Nau extensions loading...")
