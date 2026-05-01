import hashlib
import json
from datetime import date as date_class
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Expense, IdempotencyRecord


def serialize_expense(expense):
    return {
        "id": expense.id,
        "amount": str(expense.amount),
        "category": expense.category,
        "description": expense.description,
        "date": expense.date.isoformat(),
        "created_at": expense.created_at.isoformat().replace("+00:00", "Z"),
    }


def parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def normalize_payload(payload):
    return {
        "amount": str(payload["amount"]),
        "category": payload["category"],
        "description": payload["description"],
        "date": payload["date"],
    }


def payload_hash(normalized_payload):
    raw = json.dumps(normalized_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@require_http_methods(["GET"])
def api_root(request):
    return JsonResponse(
        {
            "service": "personal-finance-tool",
            "endpoints": {
                "GET /expenses": "List expenses",
                "POST /expenses": "Create an expense",
            },
        }
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def expenses_collection(request):
    if request.method == "GET":
        return list_expenses(request)
    return create_expense(request)


def list_expenses(request):
    category = request.GET.get("category")
    sort = request.GET.get("sort")

    expenses = Expense.objects.all()
    if category:
        expenses = expenses.filter(category__iexact=category.strip())

    if sort in (None, "", "date_desc"):
        expenses = expenses.order_by("-date", "-created_at", "-id")
    else:
        return JsonResponse(
            {"detail": "Unsupported sort value. Use sort=date_desc."}, status=400
        )

    items = [serialize_expense(expense) for expense in expenses]
    total = sum((expense.amount for expense in expenses), Decimal("0.00"))

    return JsonResponse(
        {"expenses": items, "total": str(total.quantize(Decimal("0.01")))}
    )


def create_expense(request):
    payload = parse_json_body(request)
    if payload is None:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)

    errors = {}
    amount = None
    expense_date = None

    raw_amount = payload.get("amount")
    try:
        amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
        if amount <= 0:
            errors["amount"] = "Amount must be greater than zero."
    except (InvalidOperation, TypeError, ValueError):
        errors["amount"] = "Amount must be a valid number."

    category = str(payload.get("category", "")).strip().lower()
    if not category:
        errors["category"] = "Category is required."

    description = str(payload.get("description", "")).strip()
    if not description:
        errors["description"] = "Description is required."

    raw_date = payload.get("date")
    try:
        expense_date = date_class.fromisoformat(str(raw_date))
    except (TypeError, ValueError):
        errors["date"] = "Date must be provided as YYYY-MM-DD."

    if errors:
        return JsonResponse({"errors": errors}, status=400)

    normalized_payload = normalize_payload(
        {
            "amount": amount,
            "category": category,
            "description": description,
            "date": expense_date.isoformat(),
        }
    )
    request_hash = payload_hash(normalized_payload)
    idempotency_key = request.headers.get("Idempotency-Key", "").strip() or request_hash

    with transaction.atomic():
        record = (
            IdempotencyRecord.objects.select_for_update()
            .filter(key=idempotency_key)
            .first()
        )

        if record is not None:
            if record.request_hash != request_hash:
                return JsonResponse(
                    {"detail": "Idempotency key was reused with different data."},
                    status=409,
                )
            if record.expense_id is not None:
                return JsonResponse(
                    {"expense": serialize_expense(record.expense), "idempotent": True},
                    status=200,
                )

        expense = Expense.objects.create(
            amount=amount,
            category=category,
            description=description,
            date=expense_date,
        )

        if record is None:
            IdempotencyRecord.objects.create(
                key=idempotency_key,
                request_hash=request_hash,
                expense=expense,
            )
        else:
            record.expense = expense
            record.save(update_fields=["expense"])

    return JsonResponse({"expense": serialize_expense(expense), "idempotent": False}, status=201)
