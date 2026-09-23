"""
Report data builders. Pure functions: (period, filters) -> plain dicts/lists.

Both the HTML view and the PDF export call these, so on-screen and exported
reports can never disagree. Nothing here is persisted — a report is always
computed from live data at request time.
"""

import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from accounts.models import Role
from tutoring.models import Absence, Assignment, GoalAchievement, Session

REPORT_KINDS = [
    ("tutors", "All tutors — one row per tutor"),
    ("tutor", "One tutor and their students"),
    ("student", "One student"),
    ("all", "Everything — all tutors and all students"),
]

ZERO = Value(Decimal("0"), output_field=DecimalField())


def _period_label(start, end):
    if start.day == 1 and end == _month_end(start):
        return start.strftime("%B %Y")
    return f"{start:%b %-d, %Y} – {end:%b %-d, %Y}"


def _month_end(day):
    nxt = (day.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return nxt - datetime.timedelta(days=1)


def _assignment_rows(assignments, start, end):
    """One row per assignment with hours/absence counts inside the period."""
    in_range = Q(sessions__date__range=(start, end))
    rows = (
        assignments.select_related("tutor", "student")
        .annotate(
            hours=Coalesce(Sum("sessions__hours", filter=in_range), ZERO),
            sessions_held=Count("sessions", filter=in_range & Q(sessions__absence="")),
            tutor_absent=Count("sessions", filter=in_range & Q(sessions__absence=Absence.TUTOR_ABSENT)),
            student_absent=Count("sessions", filter=in_range & Q(sessions__absence=Absence.STUDENT_ABSENT)),
            holidays=Count("sessions", filter=in_range & Q(sessions__absence=Absence.HOLIDAY)),
        )
        .order_by("tutor__last_name", "student__last_name")
    )
    achievements = GoalAchievement.objects.filter(
        assignment__in=assignments, achieved_on__range=(start, end)
    ).select_related("goal")
    by_assignment = {}
    for ach in achievements:
        by_assignment.setdefault(ach.assignment_id, []).append(ach.goal.label)

    return [
        {
            "tutor": a.tutor.get_full_name(),
            "student": a.student.get_full_name(),
            "subject": a.subject,
            "site": a.site,
            "schedule": f"{a.days} {a.times}".strip(),
            "hours": a.hours,
            "sessions": a.sessions_held,
            "tutor_absent": a.tutor_absent,
            "student_absent": a.student_absent,
            "holidays": a.holidays,
            "goals": by_assignment.get(a.pk, []),
            "status": "Active" if a.is_active else f"Ended {a.ended_on:%b %-d, %Y}",
            "ended_in_period": a.ended_on is not None and start <= a.ended_on <= end,
        }
        for a in rows
    ]


def _totals(rows):
    return {
        "hours": sum((r["hours"] for r in rows), Decimal("0")),
        "sessions": sum(r["sessions"] for r in rows),
        "tutor_absent": sum(r["tutor_absent"] for r in rows),
        "student_absent": sum(r["student_absent"] for r in rows),
        "holidays": sum(r["holidays"] for r in rows),
        "goals": sum(len(r["goals"]) for r in rows),
        "ended": sum(1 for r in rows if r["ended_in_period"]),
    }


def _tutor_rows(start, end, tutors=None):
    """One row per tutor summarising all their assignments in the period."""
    in_range = Q(tutor_assignments__sessions__date__range=(start, end))
    qs = User.objects.filter(profile__role=Role.TUTOR)
    if tutors is not None:
        qs = qs.filter(pk__in=tutors)
    qs = qs.annotate(
        students=Count("tutor_assignments", distinct=True),
        active_students=Count("tutor_assignments", filter=Q(tutor_assignments__ended_on__isnull=True), distinct=True),
        hours=Coalesce(Sum("tutor_assignments__sessions__hours", filter=in_range), ZERO),
        sessions_held=Count("tutor_assignments__sessions", filter=in_range & Q(tutor_assignments__sessions__absence="")),
        absences=Count("tutor_assignments__sessions", filter=in_range & ~Q(tutor_assignments__sessions__absence="")),
    ).order_by("last_name", "first_name")
    goals = dict(
        GoalAchievement.objects.filter(achieved_on__range=(start, end))
        .values_list("assignment__tutor_id")
        .annotate(n=Count("id"))
    )
    return [
        {
            "tutor": t.get_full_name(),
            "email": t.email,
            "students": t.students,
            "active_students": t.active_students,
            "hours": t.hours,
            "sessions": t.sessions_held,
            "absences": t.absences,
            "goals": goals.get(t.pk, 0),
        }
        for t in qs
    ]


def _session_detail(assignments, start, end):
    """
    Every session in the period, grouped tutor → student → dated rows.
    This is the electronic equivalent of the paper form's day-by-day grid.
    """
    sessions = (
        Session.objects.filter(assignment__in=assignments, date__range=(start, end))
        .select_related("assignment__tutor", "assignment__student")
        .order_by("assignment__tutor__last_name", "assignment__student__last_name", "assignment__subject", "date")
    )
    groups = []
    for s in sessions:
        tutor_name = s.assignment.tutor.get_full_name()
        if not groups or groups[-1]["tutor"] != tutor_name:
            groups.append({"tutor": tutor_name, "students": [], "hours": Decimal("0")})
        tutor_group = groups[-1]
        key = (s.assignment.student_id, s.assignment.subject)
        if not tutor_group["students"] or tutor_group["students"][-1]["key"] != key:
            tutor_group["students"].append(
                {
                    "key": key,
                    "student": s.assignment.student.get_full_name(),
                    "subject": s.assignment.subject,
                    "rows": [],
                    "hours": Decimal("0"),
                }
            )
        student_group = tutor_group["students"][-1]
        student_group["rows"].append(
            {
                "date": s.date,
                "hours": s.hours,
                "absence": s.get_absence_display() if s.absence else "",
                "note": s.note,
            }
        )
        if s.hours:
            student_group["hours"] += s.hours
            tutor_group["hours"] += s.hours
    return groups


def build_report(kind, start, end, tutor_id=None, student_id=None):
    """Return a dict describing the report: title, period, and one or more sections of rows."""
    report = {"kind": kind, "period": _period_label(start, end), "start": start, "end": end, "sections": []}

    if kind == "tutors":
        rows = _tutor_rows(start, end)
        report["title"] = "All tutors"
        report["sections"].append({"heading": "Tutors", "columns": "tutor", "rows": rows})

    elif kind == "tutor":
        tutor = User.objects.get(pk=tutor_id, profile__role=Role.TUTOR)
        assignments = Assignment.objects.filter(tutor=tutor)
        rows = _assignment_rows(assignments, start, end)
        report["title"] = f"Tutor: {tutor.get_full_name()}"
        report["sections"].append({"heading": "Students", "columns": "assignment", "rows": rows, "totals": _totals(rows)})
        report["sections"].append(
            {"heading": "Session detail", "columns": "session_detail", "groups": _session_detail(assignments, start, end)}
        )

    elif kind == "student":
        student = User.objects.get(pk=student_id, profile__role=Role.STUDENT)
        assignments = Assignment.objects.filter(student=student)
        rows = _assignment_rows(assignments, start, end)
        report["title"] = f"Student: {student.get_full_name()}"
        report["sections"].append({"heading": "Tutors", "columns": "assignment", "rows": rows, "totals": _totals(rows)})
        sessions = Session.objects.filter(assignment__in=assignments, date__range=(start, end)).select_related(
            "assignment__tutor"
        )
        report["sections"].append(
            {
                "heading": "Sessions",
                "columns": "session",
                "rows": [
                    {
                        "date": s.date,
                        "tutor": s.assignment.tutor.get_full_name(),
                        "hours": s.hours,
                        "absence": s.get_absence_display() if s.absence else "",
                        "note": s.note,
                    }
                    for s in sessions.order_by("date")
                ],
            }
        )

    elif kind == "all":
        tutor_rows = _tutor_rows(start, end)
        rows = _assignment_rows(Assignment.objects.all(), start, end)
        report["title"] = "All tutors and students"
        report["sections"].append({"heading": "Tutors", "columns": "tutor", "rows": tutor_rows})
        report["sections"].append({"heading": "Tutor–student pairs", "columns": "assignment", "rows": rows, "totals": _totals(rows)})
        report["sections"].append(
            {
                "heading": "Session detail — every session, by tutor and student",
                "columns": "session_detail",
                "groups": _session_detail(Assignment.objects.all(), start, end),
            }
        )

    else:
        raise ValueError(f"Unknown report kind: {kind}")

    return report
