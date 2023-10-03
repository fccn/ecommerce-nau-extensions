from django.conf.urls import url

from .views import NauUserAddressCreateView

app_name = "ecommerce_nau_extensions"

urlpatterns = [
    url(
        r"user-address/create/$",
        NauUserAddressCreateView.as_view(),
        name="nau-user-address-create",
    ),
]
