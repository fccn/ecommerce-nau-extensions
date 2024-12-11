from django.conf import settings
from oscar.core.loading import get_model

Order = get_model("order", "Order")
Country = get_model("address", "Country")


def get_order(basket):
    """
    Get the Order from the basket or None if doesn't exist.
    """
    return Order.objects.filter(basket=basket).first()


def get_default_country():
    """
    Get the default country that should be used / prepopulated on the forms.
    """
    iso_3166_1_a2 = getattr(settings, 'NAU_DEFAULT_COUNTRY_ISO_3166_1_A2', 'PT')
    return Country.objects.filter(iso_3166_1_a2=iso_3166_1_a2).first()
