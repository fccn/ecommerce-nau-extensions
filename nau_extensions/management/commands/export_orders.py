"""
Export the fulfilled ecommerce orders to a JSON Lines file.

One JSON object per line, one order per object. The file is the hand-over from ecommerce to the
LMS payments plugin and is also the archive of the sales history, so it keeps every amount
(including the tax and discount split the LMS does not store) and the raw payment processor
payload.

    python manage.py export_orders --output /tmp/orders.jsonl
    python manage.py export_orders --output /tmp/orders.jsonl --site ecommerce.nau.edu.pt --with-receipt-links

Only orders in the ``Complete`` status are exported. An order with a completed refund is exported
with status ``refunded``; every other exported order has status ``paid``.
"""

import json
import logging
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from nau_extensions.financial_manager import get_receipt_link
from oscar.core.loading import get_model

from ecommerce.extensions.fulfillment.status import ORDER
from ecommerce.extensions.refund.status import REFUND

Order = get_model("order", "Order")
PaymentProcessorResponse = get_model("payment", "PaymentProcessorResponse")

log = logging.getLogger(__name__)

STATUS_PAID = "paid"
STATUS_REFUNDED = "refunded"


def _decimal(value):
    """Serialize a Decimal as a string so the amount survives the JSON round trip unchanged."""
    return str(value) if value is not None else None


def _datetime(value):
    return value.isoformat() if value else None


def _receipt_url(order):
    """Return the Financial Manager receipt link as text, or '' when it cannot be resolved."""
    content = get_receipt_link(order)
    if not content:
        return ""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    return str(content).strip().strip('"')


def _payment(order):
    """The payment source of the order and the latest raw processor payload, when any."""
    source = order.sources.select_related("source_type").first()
    response = (
        PaymentProcessorResponse.objects.filter(basket=order.basket)
        .exclude(transaction_id=None)
        .order_by("-created")
        .first()
    )
    return {
        "processor": source.source_type.name if source else "",
        "method": (source.card_type or "") if source else "",
        "reference": (source.reference or "") if source else "",
        "amount_debited": _decimal(source.amount_debited) if source else None,
        "amount_refunded": _decimal(source.amount_refunded) if source else None,
        "transaction_id": response.transaction_id if response else "",
        "response": response.response if response else None,
    }


def _line(line):
    product = line.product
    course = getattr(product, "course", None) if product else None
    certificate_type = getattr(product.attr, "certificate_type", "") if product else ""
    return {
        "sku": line.partner_sku or "",
        "title": line.title,
        "course_id": course.id if course else "",
        "certificate_type": certificate_type or "",
        "quantity": line.quantity,
        "unit_price_incl_tax": _decimal(line.unit_price_incl_tax),
        "unit_price_excl_tax": _decimal(line.unit_price_excl_tax),
        "line_price_incl_tax": _decimal(line.line_price_incl_tax),
        "line_price_excl_tax": _decimal(line.line_price_excl_tax),
        "line_price_before_discounts_incl_tax": _decimal(line.line_price_before_discounts_incl_tax),
        "line_price_before_discounts_excl_tax": _decimal(line.line_price_before_discounts_excl_tax),
    }


def _status(order):
    if order.refunds.filter(status=REFUND.COMPLETE).exists():
        return STATUS_REFUNDED
    return STATUS_PAID


def export_order(order, with_receipt_links=False):
    """Map one ecommerce order onto the export record."""
    user = order.user
    return {
        "number": order.number,
        "status": _status(order),
        "site": order.site.domain if order.site else "",
        "user": {
            "lms_user_id": user.lms_user_id if user else None,
            "username": user.username if user else "",
            "email": user.email if user else order.guest_email,
        },
        "currency": order.currency,
        "total_incl_tax": _decimal(order.total_incl_tax),
        "total_excl_tax": _decimal(order.total_excl_tax),
        "date_placed": _datetime(order.date_placed),
        "payment": _payment(order),
        "receipt_url": _receipt_url(order) if with_receipt_links else "",
        "lines": [_line(line) for line in order.lines.select_related("product").all()],
    }


class Command(BaseCommand):
    """Export the fulfilled orders as JSON Lines."""

    help = "Export the orders in the Complete status to a JSON Lines file, one order per line."

    def add_arguments(self, parser):
        parser.add_argument("--output", help="File to write; defaults to standard output")
        parser.add_argument("--site", help="Only orders placed on this site domain")
        parser.add_argument(
            "--skip-free", action="store_true", default=False, help="Leave out the orders with a zero total"
        )
        parser.add_argument(
            "--with-receipt-links",
            action="store_true",
            default=False,
            help="Resolve the Financial Manager receipt link of every order (one HTTP request per order)",
        )

    def handle(self, *args, **options):
        orders = (
            Order.objects.filter(status=ORDER.COMPLETE)
            .select_related("user", "site", "basket")
            .order_by("date_placed", "id")
        )
        if options["site"]:
            orders = orders.filter(site__domain=options["site"])
        if options["skip_free"]:
            orders = orders.exclude(total_incl_tax=Decimal("0"))

        output = options["output"]
        stream = open(output, "w", encoding="utf-8") if output else self.stdout  # pylint: disable=consider-using-with
        exported = 0
        try:
            for order in orders.iterator():
                record = export_order(order, with_receipt_links=options["with_receipt_links"])
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                exported += 1
        except Exception as error:
            raise CommandError(f"Export stopped after {exported} orders: {error}") from error
        finally:
            if output:
                stream.close()

        skipped = Order.objects.exclude(status=ORDER.COMPLETE).count()
        self.stderr.write(f"Exported {exported} orders; {skipped} orders not in status {ORDER.COMPLETE} were left out")
