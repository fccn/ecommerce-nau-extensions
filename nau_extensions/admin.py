from pprint import pformat

from django.contrib import admin
from django.utils.html import format_html

from .models import BasketBillingInformation, BasketTransactionIntegration

admin.site.register(BasketBillingInformation)


@admin.register(BasketTransactionIntegration)
class BasketTransactionIntegrationAdmin(admin.ModelAdmin):
    list_filter = ('state',)
    search_fields = ('basket', 'state',)
    list_display = ('basket', 'state', 'created')
    fields = ('basket', 'state', 'created', 'formatted_request', 'formatted_response')
    readonly_fields = ('basket', 'state', 'created', 'formatted_request', 'formatted_response')
    show_full_result_count = False

    def formatted_request(self, obj):
        pretty_response = pformat(obj.request)

        # Use format_html() to escape user-provided inputs, avoiding an XSS vulnerability.
        return format_html('<br><br><pre>{}</pre>', pretty_response)

    def formatted_response(self, obj):
        pretty_response = pformat(obj.response)

        # Use format_html() to escape user-provided inputs, avoiding an XSS vulnerability.
        return format_html('<br><br><pre>{}</pre>', pretty_response)
