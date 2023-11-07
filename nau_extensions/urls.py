from django.conf.urls import url

from .views import (BasketBillingInformationAddressCreateUpdateView,
                    BasketBillingInformationVATINCreateUpdateView)

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
]
