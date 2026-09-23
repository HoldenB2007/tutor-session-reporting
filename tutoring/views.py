import datetime

from django.conf import settings
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from accounts.decorators import role_required
from accounts.models import Role

from .forms import EndForm, GoalsForm, ScheduleForm, SessionForm
from .models import Assignment, GoalCategory


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
    return render(
        request,
        "tutoring/tutor_home.html",
        {"assignments": assignments, "filters": filters, "staff_email": settings.STAFF_CONTACT_EMAIL},
    )


@role_required(Role.TUTOR)
def tutor_grid(request):
    """HTMX partial: just the grid, re-rendered as filters change."""
    assignments, _ = _filtered_assignments(request)
    return render(request, "tutoring/partials/student_grid.html", {"assignments": assignments})


@role_required(Role.STUDENT)
def student_home(request):
    """
    Sidebar lists every tutor this student has (active and ended); the main panel
    shows the selected assignment's hours, sessions, goals, and meeting details.
    """
    assignments = list(
        _with_totals(Assignment.objects.filter(student=request.user)).order_by("ended_on", "tutor__last_name")
    )
    total_hours = sum((a.total_hours or 0) for a in assignments)

    selected = None
    if assignments:
        wanted = request.GET.get("a")
        selected = next((a for a in assignments if str(a.pk) == wanted), assignments[0])

    context = {
        "assignments": assignments,
        "total_hours": total_hours,
        "selected": selected,
        "sessions": selected.sessions.all()[:25] if selected else [],
        "achievements": selected.achievements.select_related("goal") if selected else [],
        "staff_email": settings.STAFF_CONTACT_EMAIL,
    }
    return render(request, "tutoring/student_home.html", context)


# --- Tutor popup actions ---------------------------------------------------------
# Every action loads into the shared <dialog> via HTMX. On success the view returns
# 204 with HX-Trigger so the page closes the modal and refreshes the grid.


def _own_assignment(request, pk):
    """Scope every lookup to the logged-in tutor so IDs can't be guessed across tutors."""
    return get_object_or_404(_with_totals(Assignment.objects.filter(tutor=request.user)), pk=pk)


def _done():
    response = HttpResponse(status=204)
    response["HX-Trigger"] = "closeModal, refreshGrid"
    return response


@role_required(Role.TUTOR)
def assignment_menu(request, pk):
    assignment = _own_assignment(request, pk)
    return render(request, "tutoring/partials/menu.html", {"a": assignment})


@role_required(Role.TUTOR)
def session_history(request, pk):
    """Read-only log of every session and goal for this student, newest first, with monthly hour totals."""
    assignment = _own_assignment(request, pk)
    sessions = list(assignment.sessions.all())
    months = []
    for s in sessions:
        key = s.date.strftime("%B %Y")
        if not months or months[-1]["label"] != key:
            months.append({"label": key, "rows": [], "hours": 0, "absences": 0})
        months[-1]["rows"].append(s)
        if s.hours:
            months[-1]["hours"] += s.hours
        else:
            months[-1]["absences"] += 1
    return render(
        request,
        "tutoring/partials/history.html",
        {"a": assignment, "months": months, "achievements": assignment.achievements.select_related("goal")},
    )


@role_required(Role.TUTOR)
def log_session(request, pk):
    assignment = _own_assignment(request, pk)
    form = SessionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.instance.assignment = assignment
        form.save()
        return _done()
    return render(request, "tutoring/partials/log_session.html", {"a": assignment, "form": form})


@role_required(Role.TUTOR)
def update_goals(request, pk):
    assignment = _own_assignment(request, pk)
    form = GoalsForm(assignment, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return _done()
    # Group the checkbox widgets by category so the template mirrors the paper form.
    groups = {label: [] for _, label in GoalCategory.choices}
    for choice in form["goals"]:
        goal = choice.data["value"].instance  # ModelChoiceIteratorValue carries the Goal
        groups[goal.get_category_display()].append((choice, goal))
    return render(request, "tutoring/partials/goals.html", {"a": assignment, "form": form, "groups": groups})


@role_required(Role.TUTOR)
def update_schedule(request, pk):
    assignment = _own_assignment(request, pk)
    form = ScheduleForm(request.POST or None, instance=assignment)
    if request.method == "POST" and form.is_valid():
        form.save()
        return _done()
    return render(request, "tutoring/partials/schedule.html", {"a": assignment, "form": form})


@role_required(Role.TUTOR)
def end_tutoring(request, pk):
    assignment = _own_assignment(request, pk)
    form = EndForm(request.POST or None, instance=assignment)
    if request.method == "POST" and form.is_valid():
        form.save()
        return _done()
    return render(request, "tutoring/partials/end.html", {"a": assignment, "form": form})
