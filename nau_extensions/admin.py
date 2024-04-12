from pprint import pformat

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nau_extensions.financial_manager import \
    send_to_financial_manager_if_enabled
from nau_extensions.models import (BasketBillingInformation,
                                   BasketTransactionIntegration)

admin.site.register(BasketBillingInformation)


@admin.register(BasketTransactionIntegration)
class BasketTransactionIntegrationAdmin(admin.ModelAdmin):
    list_filter = ('state',)
    search_fields = ('basket', 'state',)
    list_display = ('basket', 'state', 'created', 'modified')
    fields = ('basket', 'state', 'created', 'modified', 'formatted_request', 'formatted_response')
    readonly_fields = ('basket', 'state', 'created', 'modified', 'formatted_request', 'formatted_response')
    show_full_result_count = False

    def formatted_request(self, obj):
        pretty_response = pformat(obj.request)

        # Use format_html() to escape user-provided inputs, avoiding an XSS vulnerability.
        return format_html('<br><br><pre>{}</pre>', pretty_response)

    def formatted_response(self, obj):
        pretty_response = pformat(obj.response)

        # Use format_html() to escape user-provided inputs, avoiding an XSS vulnerability.
        return format_html('<br><br><pre>{}</pre>', pretty_response)

    @admin.action(description=_("Retry Send to Financial Manager System"))
    def retry_send_to_financial_manager(self, request, queryset):
        """
        Django admin action that permit to retry send information to financial manager.
        """
        for bti in queryset:
            sent = send_to_financial_manager_if_enabled(bti)
            if sent:
                self.message_user(
                    request,
                    _(
                        "Retry Send to Financial Manager System with success.",
                    ),
                    messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    _(
                        "Retry Send to Financial Manager System with an error.",
                    ),
                    messages.ERROR,
                )

    actions = [retry_send_to_financial_manager]
