from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from .vatin import check_country_vatin

from oscar.core.loading import get_model

Basket = get_model("basket", "Basket")
Country = get_model("address", "Country")

from oscar.apps.address.abstract_models import AbstractAddress


class BasketBillingInformation(AbstractAddress):
    """
    Model with billing information related to the Basket.
    """
    basket = models.OneToOneField(Basket, on_delete=models.CASCADE, primary_key=True, related_name="basket_billing_information")
    # if basket get deleted, also delete BasketAdditionalBillingInformation model.

    # country = models.ForeignKey(
    #     Country, on_delete=models.CASCADE, verbose_name=_("Country")
    # )

    # A value-added tax identification number or VAT identification number (VATIN[1])
    # is an identifier used in many countries, including the countries of the European Union,
    # for value-added tax purposes.
    # Reference: https://en.wikipedia.org/wiki/VAT_identification_number
    vatin = models.CharField(
        verbose_name=_("VAT Identification Number (VATIN)"),
        max_length=255,
        blank=True,
        help_text=_(
            "The value-added tax identification number or VAT identification number "
            "can be used to identify a business or a taxable person "
            "in the European Union."
        ),
    )

    class Meta:
        verbose_name = _('Basket Billing Information')
        verbose_name_plural = _('Basket Billing Informations')

    @property
    def country_vatin(self):
        return self.country.iso_3166_1_a2 + self.vatin

    def __str__(self):
        return "%(country_vatin)s basket %(basket)s" \
            % {'country_vatin': self.country_vatin,
               'basket': self.basket,
            }

    def clean(self):
        errors = {}
        if self.vatin:
            if not check_country_vatin(
                self.country.iso_3166_1_a2, self.vatin
            ):
                msg = _("Incorrect vatin format for country")
                errors["country"] = msg
                errors["vatin"] = msg
            if errors:
                raise ValidationError(errors)

    def active_address_fields_except_country(self):
        """
        Returns the non-empty components of the address, except the country.
        """
        fields = self.base_fields.remove("country")
        return self.get_address_field_values(fields)
