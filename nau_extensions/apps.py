"""
NAU extensions of Open edX ecommerce.
"""
from django.apps import AppConfig


class NauExtensionsConfig(AppConfig):
    """
    NAU Extensions for the Open edX Ecommerce.
    """

    name = "nau_extensions"
    verbose_name = "NAU extensions app"
    plugin_app = {
        "url_config": {
            "ecommerce": {
                "namespace": "ecommerce_nau_extensions",
            }
        },
    }

    def ready(self):
        print("Nau extensions loading...")

        # Fix the incompatibility of installed packages "rest_framework" and "Markdown":
        #   md.preprocessors.register(CodeBlockPreprocessor(), 'highlight', 40)
        # Disable the rest_framework to use the markdown.
        from rest_framework import \
            compat  # pylint: disable=import-outside-toplevel
        compat.md_filter_add_syntax_highlight = lambda md: False

        # Register signals
        import nau_extensions.signals  # pylint: disable=import-outside-toplevel,unused-import
