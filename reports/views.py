from django.http import HttpResponse
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Role

from .forms import ReportForm
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
