"""
Paygate payment processing views in these views the callback pages will be implemented
"""
from abc import abstractmethod
import logging

from django.http import HttpResponseForbidden, HttpResponse
from django import shortcuts
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from oscar.core.loading import get_class, get_model

from .forms import (
    BasketBillingInformationAddressForm,
    BasketBillingInformationVATINForm,
)
from .models import BasketBillingInformation

logger = logging.getLogger(__name__)

UserAddress = get_model("address", "UserAddress")
Basket = get_model("basket", "Basket")

AbstractAddressForm = get_class("address.forms", "AbstractAddressForm")


class BasketBillingInformationCreateUpdateView(generic.UpdateView):
    success_url = "/basket/"

    def get_object(self, queryset=None):
        try:
            bbi, created = BasketBillingInformation.objects.get_or_create(
                basket=self.basket
            )
        except AttributeError:
            return None
        return bbi

    def get(self, request, *args, **kwargs):
        self.basket = shortcuts.get_object_or_404(
            Basket, pk=request.GET.get("basket_id")
        )
        if self.basket.owner != request.user:
            return HttpResponseForbidden("You need to be the owner of the Basket")
        if hasattr(self.basket, "order"):
            return HttpResponse(
                "You can't change the billing information of a basket already ordered",
                status=409,
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.basket = shortcuts.get_object_or_404(
            Basket, pk=request.POST.get("basket_id")
        )
        if self.basket.owner != request.user:
            return HttpResponseForbidden("You need to be the owner of the Basket")
        if hasattr(self.basket, "order"):
            return HttpResponse(
                "You can't change the billing information of a basket already ordered",
                status=409,
            )
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["basket"] = self.basket
        return kwargs

    def get_initial(self):
        """
        Load previous basket billing information from previous basket of same owner, load only
        some fields related to the form.
        """
        dict = super().get_initial()
        data = {}

        def get_attrs(object, attrs=[]):
            """
            If the object has any attributes.
            
            Returns:
                data (dict): the key - value of the attributes and its value.
            """
            data = {}
            if object:
                for attr in attrs:
                    value = getattr(object, attr)
                    if value:
                        data[attr] = value
            return data
        
        def _previous_bbi(basket):
            """
            Get the previous BasketBillingInformation for a previous basket of the requested user.
            """
            return (
                BasketBillingInformation.objects.filter(basket__owner=basket.owner)
                    .exclude(basket=basket)
                    .select_related("basket")
                    .order_by("-basket__id")
                    .first()
                )

        bbi = None
        try:
            bbi = BasketBillingInformation.objects.get(basket=self.basket)
        except BasketBillingInformation.DoesNotExist:
            pass
        
        data = get_attrs(bbi, self.get_fields_decide_which_bbi_to_use())
        if len(data) == 0:
            bbi = _previous_bbi(self.basket)

        if bbi:
            data = get_attrs(bbi, self.get_initial_fields())

        return {**dict, **data}

    @abstractmethod
    def get_initial_fields(self):
        """
        The fields that are going to be used on the `get_initial` method, used to pre-populate the
        form.
        """
        pass
    
    def get_fields_decide_which_bbi_to_use(self):
        """
        The fields that we use do decide witch BasketBillingInformation should we use.
        We need this, because the country field is shared between Address and VATIN.
        """
        fields = self.get_initial_fields()
        fields.remove('country')
        return fields

class BasketBillingInformationAddressCreateUpdateView(
    BasketBillingInformationCreateUpdateView, AbstractAddressForm
):
    """
    Create or Update an address on the basket billing information object.
    """

    template_name = "nau_extensions/checkout/basket_billing_information/address.html"
    form_class = BasketBillingInformationAddressForm

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return super().get_success_url()

    def get_initial_fields(self):
        """
        The fields from the address that are going to prepopulate the form.
        """
        return [
                "title",
                "first_name",
                "last_name",
                "line1",
                "line2",
                "line3",
                "line4",
                "state",
                "postcode",
                "country",
            ]


class BasketBillingInformationVATINCreateUpdateView(
    BasketBillingInformationCreateUpdateView
):
    """
    Create an Basket Billing Information
    """

    template_name = "nau_extensions/checkout/basket_billing_information/vatin.html"
    form_class = BasketBillingInformationVATINForm

    def get_initial_fields(self):
        """
        The fields that are going to prepopulate the form.
        """
        return ["country", "vatin"]

    def get_success_url(self):
        messages.info(self.request, _("VATIN saved"))
        return super().get_success_url()
