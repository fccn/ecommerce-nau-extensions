from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from oscar.apps.address.abstract_models import AbstractAddress
from oscar.core.loading import get_class, get_model

from .vatin import check_country_vatin

Basket = get_model("basket", "Basket")
Country = get_model("address", "Country")
Selector = get_class('partner.strategy', 'Selector')


class BasketBillingInformation(AbstractAddress):
    """
    Model with billing information related to the Basket.
    """

    basket = models.OneToOneField(
        Basket,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="basket_billing_information",
    )
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
        verbose_name = _("Basket Billing Information")
        verbose_name_plural = _("Basket Billing Informations")

    @property
    def country_vatin(self):
        return self.country.iso_3166_1_a2 + self.vatin

    def __str__(self):
        return "%(country_vatin)s basket %(basket)s" % {
            "country_vatin": self.country_vatin,
            "basket": self.basket,
        }

    def clean(self):
        # to check postcode
        if self.postcode:
            super().clean()

        errors = {}
        if self.vatin:
            if not check_country_vatin(self.country.iso_3166_1_a2, self.vatin):
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


class BasketTransactionIntegration(models.Model):
    """
    Model to save the information for each transaction that we receive money and that we need to
    issue a new receipt using the NAU-Financial-Manager service.
    """
    TO_BE_SENT = "To be sent"
    SENT_WITH_SUCCESS = "Sent with success"
    SENT_WITH_ERROR = "Sent with error"
    state_choices = (
        (TO_BE_SENT, _("To be sent")),
        (SENT_WITH_SUCCESS, _("Sent with success")),
        (SENT_WITH_ERROR, _("Sent with error")),
    )

    # the one-to-one relation with the basket
    basket = models.OneToOneField(
        Basket,
        on_delete=models.SET_NULL,
        null=True,
        related_name="basket_transaction_integration",
    )

    # an enumeration of possible states of the integration
    state = models.CharField(
        max_length=255, default=TO_BE_SENT, blank=False, choices=state_choices
    )

    # the request information that will be send to the nau-financial-manager
    request = JSONField()

    # the reponse that we receive from the nau-financial-manager
    response = JSONField()

    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        get_latest_by = 'created'

    @staticmethod
    def create(basket):
        """
        Create a new basket transaction integration for a basket.
        """
        return BasketTransactionIntegration(basket=basket)

    def _get_request_data(self) -> dict:
        transaction_id = self.basket.order_number
        client_name = self.basket.owner.full_name
        email = self.basket.owner.email
        address_line_1 = self.basket.basket_billing_information.line1
        address_line_2 = self.basket.basket_billing_information.line2
        if self.basket.basket_billing_information.line3 and len(self.basket.basket_billing_information.line3) > 0:
            address_line_2 += ", "
            address_line_2 += self.basket.basket_billing_information.line3
        city = self.basket.basket_billing_information.line4
        postal_code = self.basket.basket_billing_information.postcode
        state = self.basket.basket_billing_information.state
        country_code = self.basket.basket_billing_information.country.iso_3166_1_a2
        vat_identification_number = self.basket.basket_billing_information.vatin
        vat_identification_country = self.basket.basket_billing_information.country.iso_3166_1_a2
        total_amount_exclude_vat = self.basket.total_excl_tax
        total_amount_include_vat = self.basket.total_incl_tax
        currency = self.basket.currency

        return {
            "transaction_id": transaction_id,
            "client_name": client_name,
            "email": email,
            "address_line_1": address_line_1,
            "address_line_2": address_line_2,
            "city": city,
            "postal_code": postal_code,
            "state": state,
            "country_code": country_code,
            "vat_identification_number": vat_identification_number,
            "vat_identification_country": vat_identification_country,
            "total_amount_exclude_vat": total_amount_exclude_vat,
            "total_amount_include_vat": total_amount_include_vat,
            "currency": currency,
        }

    def send_to_financial_manager(self):
        # initialize strategy
        self.basket.strategy = Selector().strategy(user=self.basket.owner)

        self.request = self._get_request_data()
        self.save()

        # requests ...

        # self.response = response_data
