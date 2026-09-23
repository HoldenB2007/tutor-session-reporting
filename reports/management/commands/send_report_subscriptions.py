"""
Placeholder for automated monthly delivery.

Builds last month's report for every subscription and reports what would be sent.
Actual sending is intentionally not implemented yet — wiring it up means:
  1. an email backend (SMTP or an API provider) configured via environment variables,
  2. a scheduler calling this command on the 1st of each month (GitHub Actions cron
     hitting the Railway service, or a Railway cron job).
"""

import datetime

from django.core.management.base import BaseCommand

from reports.models import ReportSubscription
from reports.pdf import render_pdf
from reports.queries import _month_end, build_report


class Command(BaseCommand):
    help = "Show (not send) last month's report for each subscription."

    def handle(self, *args, **options):
        today = datetime.date.today()
        last_month_end = today.replace(day=1) - datetime.timedelta(days=1)
        start = last_month_end.replace(day=1)
        end = _month_end(start)

        subs = ReportSubscription.objects.all()
        if not subs:
            self.stdout.write("No subscriptions.")
            return
        for sub in subs:
            # Per-tutor / per-student kinds need a target; subscriptions only cover program-wide reports for now.
            if sub.kind not in ("tutors", "all"):
                self.stdout.write(f"skip  {sub}: per-person reports aren't subscribable yet")
                continue
            pdf = render_pdf(build_report(sub.kind, start, end))
            self.stdout.write(f"would send  {sub.email}  ←  {sub.get_kind_display()} for {start:%B %Y}  ({len(pdf)} bytes)")
        self.stdout.write(self.style.WARNING("Dry run only — email delivery is not configured."))
