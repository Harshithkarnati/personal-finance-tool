from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Expense


class ExpenseApiTests(TestCase):
    def test_create_is_idempotent_for_retry_same_payload(self):
        payload = {
            "amount": "123.45",
            "category": "Food",
            "description": "Lunch",
            "date": "2026-05-01",
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "retry-1"}

        first = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
            **headers,
        )
        second = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
            **headers,
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(second.json()["expense"]["amount"], "123.45")

    def test_get_filters_and_sorts_expenses(self):
        Expense.objects.create(
            amount=Decimal("20.00"),
            category="Travel",
            description="Taxi",
            date="2026-04-28",
        )
        Expense.objects.create(
            amount=Decimal("10.00"),
            category="Food",
            description="Coffee",
            date="2026-04-30",
        )
        Expense.objects.create(
            amount=Decimal("5.00"),
            category="Food",
            description="Snack",
            date="2026-05-01",
        )

        response = self.client.get(reverse("expenses-collection"), {"category": "Food", "sort": "date_desc"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual([expense["description"] for expense in body["expenses"]], ["Snack", "Coffee"])
        self.assertEqual(body["total"], "15.00")

    def test_negative_amount_rejected(self):
        """Negative amounts should be rejected with 400 error."""
        payload = {
            "amount": "-10.00",
            "category": "food",
            "description": "Invalid negative",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.json()["errors"])
        self.assertIn("greater than zero", response.json()["errors"]["amount"])

    def test_zero_amount_rejected(self):
        """Zero amounts should be rejected with 400 error."""
        payload = {
            "amount": "0",
            "category": "food",
            "description": "Invalid zero",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.json()["errors"])

    def test_uppercase_category_normalized_to_lowercase(self):
        """Categories should be normalized to lowercase."""
        payload = {
            "amount": "15.00",
            "category": "FOOD",
            "description": "Uppercase category",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["expense"]["category"], "food")

    def test_mixed_case_category_normalized(self):
        """Mixed case categories should be normalized to lowercase."""
        payload = {
            "amount": "20.00",
            "category": "TrAnSpOrT",
            "description": "Mixed case",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["expense"]["category"], "transport")

    def test_empty_category_rejected(self):
        """Empty or whitespace-only category should be rejected."""
        payload = {
            "amount": "10.00",
            "category": "   ",
            "description": "Test",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("category", response.json()["errors"])

    def test_empty_description_rejected(self):
        """Empty or whitespace-only description should be rejected."""
        payload = {
            "amount": "10.00",
            "category": "food",
            "description": "   ",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("description", response.json()["errors"])

    def test_missing_amount_rejected(self):
        """Missing amount field should be rejected."""
        payload = {
            "category": "food",
            "description": "Test",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.json()["errors"])

    def test_invalid_amount_format_rejected(self):
        """Invalid amount format should be rejected."""
        payload = {
            "amount": "not_a_number",
            "category": "food",
            "description": "Test",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount", response.json()["errors"])

    def test_invalid_date_format_rejected(self):
        """Invalid date format should be rejected."""
        payload = {
            "amount": "10.00",
            "category": "food",
            "description": "Test",
            "date": "05/01/2026",  # Wrong format
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("date", response.json()["errors"])

    def test_missing_date_rejected(self):
        """Missing date field should be rejected."""
        payload = {
            "amount": "10.00",
            "category": "food",
            "description": "Test",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("date", response.json()["errors"])

    def test_idempotency_different_data_conflict(self):
        """Reusing idempotency key with different data should return 409."""
        key = "conflict-test"
        payload1 = {
            "amount": "10.00",
            "category": "food",
            "description": "First",
            "date": "2026-05-01",
        }
        payload2 = {
            "amount": "20.00",
            "category": "food",
            "description": "Second",
            "date": "2026-05-01",
        }

        # First request
        self.client.post(
            reverse("expenses-collection"),
            data=payload1,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

        # Second request with same key but different data
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload2,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=key,
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("reused", response.json()["detail"].lower())

    def test_category_filter_case_insensitive(self):
        """Category filter should be case-insensitive."""
        Expense.objects.create(
            amount=Decimal("10.00"),
            category="food",
            description="Test",
            date="2026-05-01",
        )
        
        # Filter with uppercase
        response = self.client.get(reverse("expenses-collection"), {"category": "FOOD"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["expenses"]), 1)

        # Filter with mixed case
        response = self.client.get(reverse("expenses-collection"), {"category": "FoOd"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["expenses"]), 1)

    def test_invalid_sort_parameter_rejected(self):
        """Invalid sort parameter should return 400."""
        response = self.client.get(reverse("expenses-collection"), {"sort": "invalid_sort"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("sort", response.json()["detail"].lower())

    def test_amount_with_many_decimals_quantized(self):
        """Amounts with many decimals should be quantized to 2 places."""
        payload = {
            "amount": "10.12345",
            "category": "food",
            "description": "Test precision",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["expense"]["amount"], "10.12")

    def test_large_amount_accepted(self):
        """Large but valid amounts should be accepted."""
        payload = {
            "amount": "9999999.99",
            "category": "investment",
            "description": "Large expense",
            "date": "2026-05-01",
        }
        response = self.client.post(
            reverse("expenses-collection"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["expense"]["amount"], "9999999.99")
