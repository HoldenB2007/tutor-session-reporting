from django.contrib import admin
from django.urls import include, path

from accounts import views as account_views

from . import views

urlpatterns = [
    path("", account_views.home, name="home"),
    path("healthz/", views.healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("tutoring.urls")),
    path("", include("reports.urls")),
]
