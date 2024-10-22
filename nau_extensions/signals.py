import re

from django.db.models.signals import pre_save
from django.dispatch import receiver
from nau_extensions.financial_manager import \
    send_to_financial_manager_if_enabled
from nau_extensions.models import BasketTransactionIntegration
from oscar.core.loading import get_class, get_model

post_checkout = get_class("checkout.signals", "post_checkout")
Product = get_model('catalogue', 'Product')


@receiver(
    post_checkout,
    dispatch_uid="create_and_send_basket_transaction_integration_to_financial_manager",
)
# @silence_exceptions("Failed to create and send basket transaction integration to financial manager.")
def create_and_send_basket_transaction_integration_to_financial_manager(
    sender, order=None, request=None, **kwargs
):  # pylint: disable=unused-argument
    """
    Create a Basket Transaction Integration object after a checkout of an Order;
    then send that information to the nau-financial-manager service.
    """
    bti: BasketTransactionIntegration = BasketTransactionIntegration.create(order.basket)
    bti.save()
    bti.refresh_from_db()
    send_to_financial_manager_if_enabled(bti)


@receiver(pre_save, sender=Product)
def change_product_titles(sender, instance, *_args, **kwargs):
    """
    Change Product title that is hardcoded in English.
    So we just find and replace the English words to Portuguese on the Product title field.
    Also remove the `verified` word, because on NAU this doesn't make sense.
    Hardcoded code locations:
    - https://github.com/fccn/ecommerce/blob/132e45e7af964c9addbe97deae6ab4327caa6cce/ecommerce/courses/models.py#L57
    - https://github.com/fccn/ecommerce/blob/132e45e7af964c9addbe97deae6ab4327caa6cce/ecommerce/courses/models.py#L295
    - https://github.com/fccn/ecommerce/blob/132e45e7af964c9addbe97deae6ab4327caa6cce/ecommerce/courses/models.py#L134
    - https://github.com/fccn/ecommerce/blob/132e45e7af964c9addbe97deae6ab4327caa6cce/ecommerce/courses/models.py#L131
    """
    new_title = instance.title
    new_title = new_title.replace('Seat in', 'Lugar em')
    new_title = new_title.replace('Enrollment code for verified seat in', 'Código de inscrição para')
    new_title = new_title.replace('with verified certificate', 'com certificado pago')
    new_title = new_title.replace('with honor certificate', 'com certificado grátis')
    instance.title = new_title
