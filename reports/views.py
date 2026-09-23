from django.contrib.auth.models import User
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Role
from tutoring.models import Assignment, Session


@role_required(Role.STAFF)
def staff_home(request):
    context = {
        "tutor_count": User.objects.filter(profile__role=Role.TUTOR).count(),
        "student_count": User.objects.filter(profile__role=Role.STUDENT).count(),
        "active_assignments": Assignment.objects.filter(ended_on__isnull=True).count(),
        "session_count": Session.objects.count(),
    }
    return render(request, "reports/staff_home.html", context)
