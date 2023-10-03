from oscar.core.loading import get_class
from django.conf.urls import url
from django.urls import path
from .views import NauUserAddressCreateView

app_name = "ecommerce_nau_extensions"

urlpatterns = [
    # Shipping/user address views
    # url(r'shipping-address/$',
    #     shipping_address_view.as_view(), name='shipping-address'),
    
    url(r'user-address/create/$',
        NauUserAddressCreateView.as_view(),
        name='nau-user-address-create'),
    
    # url(r'user-address/create/(?P<pk>\d+)/$',
        # # NauUserAddressUpdateView.as_view(),
        # name='user-address-update'),
    

    # url(r'user-address/delete/(?P<pk>\d+)/$',
    #     user_address_delete_view.as_view(),
    #     name='user-address-delete'),
]
