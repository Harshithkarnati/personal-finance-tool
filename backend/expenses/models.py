from django.db import models


class Expense(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=120, db_index=True)
    description = models.TextField()
    date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at", "-id"]


class IdempotencyRecord(models.Model):
    key = models.CharField(max_length=255, unique=True)
    request_hash = models.CharField(max_length=64)
    expense = models.OneToOneField(
        Expense,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="idempotency_record",
    )
    created_at = models.DateTimeField(auto_now_add=True)
