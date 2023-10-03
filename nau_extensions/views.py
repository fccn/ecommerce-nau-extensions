"""
Paygate payment processing views in these views the callback pages will be implemented
"""
import logging

from django.views import generic
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import UserAddressForm

from oscar.core.loading import get_class, get_model

logger = logging.getLogger(__name__)

UserAddress = get_model('address', 'UserAddress')

AbstractAddressForm = get_class('address.forms', 'AbstractAddressForm')


class NauUserAddressCreateView(generic.CreateView, AbstractAddressForm):
    """
    Create an user address
    """

    template_name = "nau_extensions/checkout/user_address_form.html"
    form_class = UserAddressForm
    success_url = "/basket/"

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_default_for_billing"] = True
        return kwargs
    
    def get_initial(self):
        dict = super().get_initial()

        user_address = None
        try:
            user_address = self.request.user.addresses.get(is_default_for_billing=True)
        except UserAddress.DoesNotExist:
            pass

        if user_address:
            previous = {
                'title': user_address.title, 
                'first_name': user_address.first_name, 
                'last_name': user_address.last_name,
                'line1': user_address.line1, 
                'line2': user_address.line2, 
                'line3': user_address.line3, 
                'line4': user_address.line4,
                'state': user_address.state, 
                'postcode': user_address.postcode, 
                'country': user_address.country,
            }
        else:
            previous = {}
        return {**dict, **previous}

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return super().get_success_url()
