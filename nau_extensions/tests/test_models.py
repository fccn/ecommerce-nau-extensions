from nau_extensions.models import BasketTransactionIntegration

from ecommerce.extensions.test.factories import create_order
from ecommerce.tests.factories import UserFactory
from ecommerce.tests.testcases import TestCase


class ModelsNAUExtensionsTests(TestCase):
    """
    This class aims to test the specifics of the nau extensions project related to django models.
    """

    def test_basket_integration_integration_create_second_same_basket(self):
        """
        Test the creation of a second `BasketTransactionIntegration` for same basket/order.
        """
        order = create_order(user=UserFactory())
        bti = BasketTransactionIntegration.create(order.basket)
        bti.save()

        # the 2nd call on create should not fail
        bti2 = BasketTransactionIntegration.create(order.basket)
        bti2.save()

        self.assertNotEqual(bti.id, None)
        self.assertEqual(bti.id, bti2.id)
