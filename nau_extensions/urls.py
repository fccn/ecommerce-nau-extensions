from django.conf.urls import url
from nau_extensions.views import (
    BasketBillingInformationAddressCreateUpdateView,
    BasketBillingInformationVATINCreateUpdateView, ReceiptLinkView)

app_name = "ecommerce_nau_extensions"

urlpatterns = [
    url(
        r"basket-billing-information/address/$",
        BasketBillingInformationAddressCreateUpdateView.as_view(),
        name="nau-basket-billing-information-address",
    ),

    url(
        r"basket-billing-information/vatin/$",
        BasketBillingInformationVATINCreateUpdateView.as_view(),
        name="nau-basket-billing-information-vatin",
    ),

    url(
        r"receipt-link/$",
        ReceiptLinkView.as_view(),
        name="receipt_link_view",
    ),

]
