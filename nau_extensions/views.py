"""
Basket billing information views.
"""
import logging
from abc import abstractmethod

from django import shortcuts
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from oscar.core.loading import get_class, get_model

from nau_extensions.forms import (BasketBillingInformationAddressForm,
                    BasketBillingInformationVATINForm)
from nau_extensions.models import BasketBillingInformation

logger = logging.getLogger(__name__)

UserAddress = get_model("address", "UserAddress")
Basket = get_model("basket", "Basket")

AbstractAddressForm = get_class("address.forms", "AbstractAddressForm")


class BasketBillingInformationCreateUpdateView(generic.UpdateView):
    """
    The merged create and update view for the `BasketBillingInformation`.
    """
    success_url = "/basket/"

    def get_object(self, queryset=None):
        try:
            bbi, created = BasketBillingInformation.objects.get_or_create(  # pylint: disable=unused-variable
                basket=self.basket
            )
        except AttributeError:
            return None
        return bbi

    def get(self, request, *args, **kwargs):
        self.basket = shortcuts.get_object_or_404(  # pylint: disable=attribute-defined-outside-init
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
        self.basket = shortcuts.get_object_or_404(  # pylint: disable=attribute-defined-outside-init
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
        _dict = super().get_initial()
        data = {}

        def get_attrs(_object, attrs=[]):  # pylint: disable=dangerous-default-value
            """
            If the object has any attributes.

            Returns:
                data (dict): the key - value of the attributes and its value.
            """
            data = {}
            if _object:
                for attr in attrs:
                    value = getattr(_object, attr)
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

        return {**_dict, **data}

    @abstractmethod
    def get_initial_fields(self):
        """
        The fields that are going to be used on the `get_initial` method, used to pre-populate the
        form.
        """
        pass  # pylint: disable=unnecessary-pass

    def get_fields_decide_which_bbi_to_use(self):
        """
        The fields that we use do decide witch BasketBillingInformation should we use.
        We need this, because the country field is shared between Address and VATIN.
        """
        fields = self.get_initial_fields()
        fields.remove("country")
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
