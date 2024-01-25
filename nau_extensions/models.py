from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from nau_extensions.utils import get_order
from nau_extensions.vatin import check_country_vatin
from oscar.apps.address.abstract_models import AbstractAddress
from oscar.core.loading import get_model

Basket = get_model("basket", "Basket")
Country = get_model("address", "Country")


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

    @classmethod
    def get_by_basket(cls, basket):
        """
        Get the `BasketBillingInformation` instance from a `basket` instance.
        This is required because the `basket` class doesn't know this one.
        And the relation basket.basket_billing_information isn't recognized
        by Django.
        """
        return BasketBillingInformation.objects.filter(basket=basket).first()


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

    # the response that we receive from the nau-financial-manager
    response = JSONField()

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = "created"

    @classmethod
    def create(cls, basket):
        """
        Create a new basket basket transaction integration or reuse an existing one for a basket.
        """
        order = get_order(basket)
        if not order:
            raise ValueError(
                f"The creation of BasketTransactionIntegration requires a basket with an order"
                f", basket '{basket}'"
            )
        bti = cls.get_by_basket(basket)
        if not bti:
            bti = BasketTransactionIntegration(basket=basket)
        return bti

    @classmethod
    def get_by_basket(cls, basket):
        """
        Get the `BasketTransactionIntegration` instance from a `basket` instance.
        This is required because the `basket` class doesn't know this one.
        And the relation basket.basket_transaction_integration isn't recognized
        by Django.
        """
        return BasketTransactionIntegration.objects.filter(basket=basket).first()
