from django import forms
from oscar.apps.address.forms import AbstractAddressForm
from oscar.core.loading import get_model

from .models import BasketBillingInformation

Basket = get_model("basket", "Basket")


class BasketBillingInformationAddressForm(AbstractAddressForm):
    """
    A custom Address Form without the fields 'phone_number' and 'notes'
    """

    class Meta:
        model = BasketBillingInformation
        fields = [
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

    def __init__(self, basket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.basket = basket


class BasketBillingInformationVATINForm(forms.ModelForm):
    """
    A form to save 'BasketBillingInformation' vatin information.
    """

    class Meta:
        model = BasketBillingInformation
        fields = ["country", "vatin"]

    def __init__(self, basket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.basket = basket

        self.fields["vatin"].required = True
