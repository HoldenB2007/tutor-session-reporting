from django.db import models

from .queries import REPORT_KINDS


class ReportSubscription(models.Model):
    """
    Placeholder for automated monthly report delivery.

    Staff can sign an address up for a report category; nothing is sent yet.
    `manage.py send_report_subscriptions` shows what *would* go out, and is the
    hook a scheduled job (e.g. GitHub Actions cron) will call once email is wired up.
    """

    email = models.EmailField()
    kind = models.CharField(max_length=10, choices=REPORT_KINDS, verbose_name="report")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("email", "kind")]
        ordering = ["email", "kind"]

    def __str__(self):
        return f"{self.email} ← {self.get_kind_display()}"
