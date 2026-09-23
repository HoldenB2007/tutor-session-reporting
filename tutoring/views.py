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


@role_required(Role.TUTOR)
def tutor_home(request):
    assignments = _with_totals(Assignment.objects.filter(tutor=request.user))
    return render(request, "tutoring/tutor_home.html", {"assignments": assignments})


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
