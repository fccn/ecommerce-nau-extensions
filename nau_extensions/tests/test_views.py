# import mock
# from django.urls import reverse
# from nau_extensions.serializers import OrderReceiptLinkSerializer

# from ecommerce.courses.tests.factories import CourseFactory
# from ecommerce.extensions.test.factories import create_basket, create_order
# from ecommerce.tests.factories import UserFactory
# from ecommerce.tests.testcases import TestCase


# class NAUExtensionsViewTests(TestCase):

#     @mock.patch.object(OrderReceiptLinkSerializer, "get_receipt_link")
#     def test_view_receipt_link(self, mock_get_receipt_link):
#         """
#         Test the Receipt Link View
#         """
#         # create data for test
#         course = CourseFactory(id='a/b/c', name='Demo Course', partner=self.partner)
#         product = course.create_or_update_seat('test-certificate-type', False, 20)
#         basket = create_basket(site=self.site, owner=UserFactory(), empty=True)
#         basket.add_product(product)
#         basket.save()

#         # Save an Order for the Basket, to mock has we already received callback.
#         order = create_order(basket=basket)
#         order.save()

#         # mock the call financial manager that will return the receipt link
#         mock_get_receipt_link.return_value = [{
#             "https://example.com/receipt-link/somedocument.pdf"
#         }]

#         response = self.client.get(
#             # reverse("ecommerce_nau_extensions:receipt_link_view")+ "?id=" + order.id,
#             f"/payment/nau_extensions/receipt-link/?id={order.id}",
#         )

#         mock_get_receipt_link.assert_called_once_with(order)

#         self.assertEqual("https://example.com/receipt-link/somedocument.pdf", response.content)
