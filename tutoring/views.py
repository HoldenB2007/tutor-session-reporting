from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Role


@role_required(Role.TUTOR)
def tutor_home(request):
    return render(request, "tutoring/tutor_home.html")


@role_required(Role.STUDENT)
def student_home(request):
    return render(request, "tutoring/student_home.html")
