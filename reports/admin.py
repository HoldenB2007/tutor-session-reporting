from django.contrib import admin

from .models import ReportSubscription


@admin.register(ReportSubscription)
class ReportSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "kind", "created_at")
    list_filter = ("kind",)
    search_fields = ("email",)
