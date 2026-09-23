from django.urls import path

from . import views

urlpatterns = [
    path("staff/", views.staff_home, name="staff_home"),
    path("staff/reports/pdf/", views.report_pdf, name="report_pdf"),
    path("staff/subscriptions/", views.subscriptions, name="subscriptions"),
]
