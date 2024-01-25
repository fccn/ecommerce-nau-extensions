from decimal import Decimal as D

from oscar.test.factories import (Basket, create_product, create_stockrecord,
                                  get_model)

from ecommerce.extensions.partner.strategy import DefaultStrategy
from ecommerce.tests.factories import SiteConfigurationFactory, UserFactory

ProductClass = get_model("catalogue", "ProductClass")


def create_basket(
    owner=None, site=None, empty=False, price="10.00", product_class=None
):  # pylint:disable=function-redefined
    """
    Create a basket for testing inside of the NAU extensions project.
    """
    if site is None:
        site = SiteConfigurationFactory().site
    if owner is None:
        owner = UserFactory()
    basket = Basket.objects.create(site=site, owner=owner)
    basket.strategy = DefaultStrategy()
    if not empty:
        if product_class:
            product_class_instance = ProductClass.objects.get(name=product_class)
            product = create_product(product_class=product_class_instance)
        else:
            product = create_product()
        create_stockrecord(product, num_in_stock=2, price_excl_tax=D(price))
        basket.add_product(product)
    return basket


class MockResponse:
    """
    A mocked requests response.
    """

    def __init__(self, json_data=None, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        """
        The Json output that will be mocked
        """
        return self.json_data

    def content(self):
        """
        The Json data
        """
        return self.json_data
