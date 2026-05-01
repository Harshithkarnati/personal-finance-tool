from django.contrib import admin

from .models import Expense, IdempotencyRecord

admin.site.register(Expense)
admin.site.register(IdempotencyRecord)
