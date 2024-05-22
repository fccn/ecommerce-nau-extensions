"""Serializers for data manipulated by ecommerce API endpoints."""

import logging

from nau_extensions.financial_manager import get_receipt_link
from oscar.core.loading import get_model
from rest_framework import serializers

logger = logging.getLogger(__name__)

Order = get_model('order', 'Order')


class OrderReceiptLinkSerializer(serializers.ModelSerializer):
    """Serializer for parsing order data with only the receipt link."""
    receipt_link = serializers.SerializerMethodField()

    def get_receipt_link(self, obj):
        # return "https://ilink.pt/xpto.pdf"
        # return None
        return get_receipt_link(obj)

    class Meta:
        model = Order
        fields = (
            'receipt_link',
        )
