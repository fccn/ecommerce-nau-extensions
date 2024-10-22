from nau_extensions.models import BasketTransactionIntegration
from oscar.core.loading import get_model

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.test.factories import create_order
from ecommerce.tests.factories import PartnerFactory, UserFactory
from ecommerce.tests.testcases import TestCase

Product = get_model('catalogue', 'Product')


class SignalsNAUExtensionsTests(TestCase):
    """
    This class aims to test the specifics of the nau extensions project related to django models.
    """

    def test_signal_receiver_create_and_send_basket_transaction_integration_to_financial_manager(self):
        """
        Test that after a checkout the `create_and_send_basket_transaction_integration_to_financial_manager`
        is trigged.
        """
        order = create_order(user=UserFactory())
        EdxOrderPlacementMixin().handle_successful_order(order)
        bti = BasketTransactionIntegration.get_by_basket(order.basket)
        self.assertTrue(bti is not None)

    def test_change_product_title_verified(self):
        """
        Test change the product hardcoded names in english to portuguese versions for verified course run.
        """
        partner = PartnerFactory(short_code="edX")
        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        product = course.create_or_update_seat("verified", False, 1)
        product.save()
        product.refresh_from_db()
        self.assertEqual(product.title, "Lugar em edX Demonstration Course com certificado pago")
        self.assertEqual(product.parent.title, "Lugar em edX Demonstration Course")

    def test_change_product_title_honor(self):
        """
        Test change the product hardcoded names in english to portuguese versions for `honor` course run.
        """
        partner = PartnerFactory(short_code="edX")
        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        honor_product = course.create_or_update_seat("honor", False, 0)
        honor_product.save()
        honor_product.refresh_from_db()
        self.assertEqual(honor_product.title, "Lugar em edX Demonstration Course com certificado grátis")
        self.assertEqual(honor_product.parent.title, "Lugar em edX Demonstration Course")

    def test_change_product_title_enrollment_code(self):
        """
        Test change the product hardcoded names in english to portuguese versions for verified course run.
        """
        partner = PartnerFactory(short_code="edX")
        course = CourseFactory(
            id="course-v1:edX+DemoX+Demo_Course",
            name="edX Demonstration Course",
            partner=partner,
        )
        product = course.create_or_update_seat("verified", False, 1, create_enrollment_code=True)
        product.save()
        enrollment_code = course.get_enrollment_code()
        self.assertEqual(enrollment_code.title, "Código de inscrição para edX Demonstration Course")
