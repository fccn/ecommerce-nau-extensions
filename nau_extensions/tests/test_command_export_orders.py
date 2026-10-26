"""Tests for the ``export_orders`` management command."""

import json
import os
import tempfile
from decimal import Decimal
from io import StringIO

import mock
from django.core.management import call_command
from nau_extensions.management.commands.export_orders import STATUS_PAID, STATUS_REFUNDED, export_order
from oscar.core.loading import get_model

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.fulfillment.status import ORDER
from ecommerce.extensions.refund.status import REFUND
from ecommerce.extensions.refund.tests.factories import RefundFactory
from ecommerce.extensions.test.factories import create_basket, create_order
from ecommerce.tests.factories import UserFactory
from ecommerce.tests.testcases import TestCase

PaymentProcessorResponse = get_model("payment", "PaymentProcessorResponse")
Source = get_model("payment", "Source")
SourceType = get_model("payment", "SourceType")

RECEIPT_LINK_PATH = "nau_extensions.management.commands.export_orders.get_receipt_link"


class ExportOrdersCommandTests(TestCase):
    """The export produces one complete, self-describing record per fulfilled order."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="learner", email="learner@example.com", lms_user_id=4242)

    def _complete_order(self, user=None, with_seat=False, price="20.00"):
        """A Complete order, optionally for a verified seat, paid with PayGate by MBWAY."""
        user = user or self.user
        if with_seat:
            course = CourseFactory(id="course-v1:NAU+Demo+2026", name="Demo Course", partner=self.partner)
            seat = course.create_or_update_seat("verified", False, Decimal(price))
            basket = create_basket(site=self.site, owner=user, empty=True)
            basket.add_product(seat)
            basket.save()
        else:
            basket = create_basket(site=self.site, owner=user, price=price)
        order = create_order(basket=basket, user=user, site=self.site)
        order.status = ORDER.COMPLETE
        order.save()
        Source.objects.create(
            order=order,
            source_type=SourceType.objects.get_or_create(name="PayGate", defaults={"code": "paygate"})[0],
            currency=order.currency,
            amount_allocated=order.total_incl_tax,
            amount_debited=order.total_incl_tax,
            reference="PG-REF-1",
            card_type="MBWAY",
        )
        PaymentProcessorResponse.objects.create(
            processor_name="paygate", transaction_id="PG-TXN-1", basket=basket, response={"STATUS_CODE": "C"}
        )
        return order

    def _run(self, *args):
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(handle)
        stderr = StringIO()
        try:
            call_command("export_orders", "--output", path, *args, stderr=stderr)
            with open(path, encoding="utf-8") as stream:
                records = [json.loads(line) for line in stream if line.strip()]
        finally:
            os.remove(path)
        return records, stderr.getvalue()

    def test_export_order_maps_every_field(self):
        order = self._complete_order(with_seat=True)

        record = export_order(order)

        self.assertEqual(record["number"], order.number)
        self.assertEqual(record["status"], STATUS_PAID)
        self.assertEqual(record["site"], self.site.domain)
        self.assertEqual(
            record["user"], {"lms_user_id": 4242, "username": "learner", "email": "learner@example.com"}
        )
        self.assertEqual(record["currency"], order.currency)
        self.assertEqual(record["total_incl_tax"], str(order.total_incl_tax))
        self.assertEqual(record["total_excl_tax"], str(order.total_excl_tax))
        self.assertEqual(record["date_placed"], order.date_placed.isoformat())
        self.assertEqual(record["receipt_url"], "")
        self.assertEqual(
            record["payment"],
            {
                "processor": "PayGate",
                "method": "MBWAY",
                "reference": "PG-REF-1",
                "amount_debited": str(order.total_incl_tax),
                "amount_refunded": "0.00",
                "transaction_id": "PG-TXN-1",
                "response": {"STATUS_CODE": "C"},
            },
        )
        line = order.lines.first()
        self.assertTrue(line.partner_sku)
        self.assertEqual(
            record["lines"],
            [
                {
                    "sku": line.partner_sku,
                    "title": line.title,
                    "course_id": "course-v1:NAU+Demo+2026",
                    "certificate_type": "verified",
                    "quantity": 1,
                    "unit_price_incl_tax": str(line.unit_price_incl_tax),
                    "unit_price_excl_tax": str(line.unit_price_excl_tax),
                    "line_price_incl_tax": str(line.line_price_incl_tax),
                    "line_price_excl_tax": str(line.line_price_excl_tax),
                    "line_price_before_discounts_incl_tax": str(line.line_price_before_discounts_incl_tax),
                    "line_price_before_discounts_excl_tax": str(line.line_price_before_discounts_excl_tax),
                }
            ],
        )

    def test_line_without_course_has_empty_course_and_certificate_type(self):
        order = self._complete_order()

        record = export_order(order)

        self.assertEqual(record["lines"][0]["course_id"], "")
        self.assertEqual(record["lines"][0]["certificate_type"], "")

    def test_order_without_payment_source_exports_empty_payment(self):
        order = create_order(user=self.user, site=self.site)
        order.status = ORDER.COMPLETE
        order.save()

        record = export_order(order)

        self.assertEqual(
            record["payment"],
            {
                "processor": "",
                "method": "",
                "reference": "",
                "amount_debited": None,
                "amount_refunded": None,
                "transaction_id": "",
                "response": None,
            },
        )

    def test_order_with_completed_refund_is_refunded(self):
        order = self._complete_order()
        RefundFactory(order=order, user=order.user, status=REFUND.COMPLETE)

        self.assertEqual(export_order(order)["status"], STATUS_REFUNDED)

    def test_order_with_open_refund_stays_paid(self):
        order = self._complete_order()
        RefundFactory(order=order, user=order.user, status=REFUND.OPEN)

        self.assertEqual(export_order(order)["status"], STATUS_PAID)

    @mock.patch(RECEIPT_LINK_PATH, return_value=b'"https://ilink.test/receipts/1"\n')
    def test_receipt_link_is_resolved_only_when_asked(self, get_receipt_link):
        order = self._complete_order()

        self.assertEqual(export_order(order)["receipt_url"], "")
        get_receipt_link.assert_not_called()

        self.assertEqual(export_order(order, with_receipt_links=True)["receipt_url"], "https://ilink.test/receipts/1")
        get_receipt_link.assert_called_once_with(order)

    @mock.patch(RECEIPT_LINK_PATH, return_value=None)
    def test_unresolved_receipt_link_is_empty(self, _):
        order = self._complete_order()

        self.assertEqual(export_order(order, with_receipt_links=True)["receipt_url"], "")

    def test_command_exports_only_complete_orders_oldest_first(self):
        older = self._complete_order()
        newer = self._complete_order(user=UserFactory(lms_user_id=99))
        open_order = create_order(user=self.user, site=self.site)
        self.assertEqual(open_order.status, ORDER.OPEN)

        records, summary = self._run()

        self.assertEqual([record["number"] for record in records], [older.number, newer.number])
        self.assertIn("Exported 2 orders; 1 orders not in status Complete were left out", summary)

    def test_command_filters_by_site(self):
        self._complete_order()

        self.assertEqual(len(self._run("--site", self.site.domain)[0]), 1)
        self.assertEqual(len(self._run("--site", "other.example.com")[0]), 0)

    def test_command_skips_free_orders_when_asked(self):
        self._complete_order(price="0.00")
        paid = self._complete_order(user=UserFactory(lms_user_id=7))

        self.assertEqual(len(self._run()[0]), 2)
        self.assertEqual([record["number"] for record in self._run("--skip-free")[0]], [paid.number])

    @mock.patch(RECEIPT_LINK_PATH, return_value="https://ilink.test/receipts/2")
    def test_command_passes_receipt_link_option(self, get_receipt_link):
        self._complete_order()

        records, _ = self._run("--with-receipt-links")

        self.assertEqual(records[0]["receipt_url"], "https://ilink.test/receipts/2")
        self.assertEqual(get_receipt_link.call_count, 1)

    def test_command_writes_to_stdout_without_output(self):
        order = self._complete_order()
        stdout = StringIO()

        call_command("export_orders", stdout=stdout, stderr=StringIO())

        self.assertEqual(json.loads(stdout.getvalue())["number"], order.number)

    @mock.patch("nau_extensions.management.commands.export_orders.export_order", side_effect=RuntimeError("boom"))
    def test_command_reports_failure(self, _):
        self._complete_order()

        with self.assertRaises(Exception) as context:
            self._run()

        self.assertIn("Export stopped after 0 orders: boom", str(context.exception))
