from django.contrib import admin
from django.urls import include, path

from expenses import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.api_root, name="api-root"),
    path("", include("expenses.urls")),
]
