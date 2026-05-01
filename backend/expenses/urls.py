from django.urls import path

from . import views

urlpatterns = [
    path("expenses", views.expenses_collection, name="expenses-collection"),
]
