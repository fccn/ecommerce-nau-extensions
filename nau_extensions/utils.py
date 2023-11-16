from oscar.core.loading import get_model

Order = get_model("order", "Order")


def get_order(basket):
    """
    Get the Order from the basket or None if doesn't exist.
    """
    return Order.objects.filter(basket=basket).first()
