"""
Paygate payment processing views in these views the callback pages will be implemented
"""
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

    def get_initial(self, fields=[]):
        """
        Load previous basket billing information from previous basket of same owner, load only
        some fields related to the form.
        """
        dict = super().get_initial()
        data = {}

        try:
            BasketBillingInformation.objects.get(basket=self.basket)
        except BasketBillingInformation.DoesNotExist:
            prev_basket_bbi = (
                BasketBillingInformation.objects.filter(basket__owner=self.request.user)
                .select_related("basket")
                .order_by("-basket__id")
                .first()
            )
            if prev_basket_bbi:
                for field in fields:
                    data[field] = getattr(prev_basket_bbi, field)

        return {**dict, **data}


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

    def get_initial(self):
        return super().get_initial(
            fields=[
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
        )


class BasketBillingInformationVATINCreateUpdateView(
    BasketBillingInformationCreateUpdateView
):
    """
    Create an Basket Billing Information
    """

    template_name = "nau_extensions/checkout/basket_billing_information/vatin.html"
    form_class = BasketBillingInformationVATINForm

    def get_initial(self):
        return super().get_initial(fields=["country", "vatin"])

    def get_success_url(self):
        messages.info(self.request, _("VATIN saved"))
        return super().get_success_url()
