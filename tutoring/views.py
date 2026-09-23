import datetime

from django.db.models import Count, Max, Q, Sum
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Role

from .models import Assignment


def _with_totals(queryset):
    """Annotate assignments with hours tutored, absence count, and last session date."""
    return queryset.select_related("tutor", "student").annotate(
        total_hours=Sum("sessions__hours"),
        absence_count=Count("sessions", filter=~Q(sessions__absence="")),
        last_session=Max("sessions__date"),
    )


def _parse_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _filtered_assignments(request):
    """Apply the grid's search / sort / date filters to the tutor's own assignments."""
    qs = _with_totals(Assignment.objects.filter(tutor=request.user))

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) | Q(subject__icontains=q)
        )

    # Date filter: only students with a session in the range.
    date_from = _parse_date(request.GET.get("from"))
    date_to = _parse_date(request.GET.get("to"))
    if date_from:
        qs = qs.filter(sessions__date__gte=date_from)
    if date_to:
        qs = qs.filter(sessions__date__lte=date_to)
    if date_from or date_to:
        qs = qs.distinct()

    sort = request.GET.get("sort", "alpha")
    if sort == "recent":
        qs = qs.order_by("-last_session", "student__last_name")
    else:
        qs = qs.order_by("student__last_name", "student__first_name")

    return qs, {"q": q, "sort": sort, "from": request.GET.get("from", ""), "to": request.GET.get("to", "")}


@role_required(Role.TUTOR)
def tutor_home(request):
    assignments, filters = _filtered_assignments(request)
    return render(request, "tutoring/tutor_home.html", {"assignments": assignments, "filters": filters})


@role_required(Role.TUTOR)
def tutor_grid(request):
    """HTMX partial: just the grid, re-rendered as filters change."""
    assignments, _ = _filtered_assignments(request)
    return render(request, "tutoring/partials/student_grid.html", {"assignments": assignments})


@role_required(Role.STUDENT)
def student_home(request):
    assignments = _with_totals(Assignment.objects.filter(student=request.user)).prefetch_related(
        "achievements__goal"
    )
    total_hours = sum((a.total_hours or 0) for a in assignments)
    return render(
        request,
        "tutoring/student_home.html",
        {"assignments": assignments, "total_hours": total_hours},
    )
