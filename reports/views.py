from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from accounts.decorators import role_required
from accounts.models import Role

from .forms import ReportForm, SubscriptionForm
from .models import ReportSubscription
from .pdf import render_pdf
from .queries import build_report


def _report_from_request(request):
    """Validate the query string; return (form, report or None)."""
    form = ReportForm(request.GET or None)
    if not (request.GET and form.is_valid()):
        return form, None
    d = form.cleaned_data
    report = build_report(
        d["kind"],
        d["start"],
        d["end"],
        tutor_id=d["tutor"].pk if d.get("tutor") else None,
        student_id=d["student"].pk if d.get("student") else None,
    )
    return form, report


@role_required(Role.STAFF)
def staff_home(request):
    form, report = _report_from_request(request)
    return render(
        request,
        "reports/staff_home.html",
        {"form": form, "report": report, "query": request.GET.urlencode()},
    )


@role_required(Role.STAFF)
def report_pdf(request):
    form, report = _report_from_request(request)
    if report is None:
        return HttpResponse("Invalid report parameters.", status=400)
    filename = f"lvaep-{report['kind']}-{report['start']:%Y%m%d}-{report['end']:%Y%m%d}.pdf"
    response = HttpResponse(render_pdf(report), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@role_required(Role.STAFF)
def subscriptions(request):
    """Sign an email up for a monthly report category. Storage only — delivery is a future step."""
    form = SubscriptionForm(request.POST or None)
    if request.method == "POST":
        if "delete" in request.POST:
            ReportSubscription.objects.filter(pk=request.POST["delete"]).delete()
            return redirect("subscriptions")
        if form.is_valid():
            form.save()
            messages.success(request, f"{form.instance.email} will receive the “{form.instance.get_kind_display()}” report monthly once delivery is enabled.")
            return redirect("subscriptions")
    return render(
        request,
        "reports/subscriptions.html",
        {"form": form, "subscriptions": ReportSubscription.objects.all()},
    )
