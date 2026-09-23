from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Role


@role_required(Role.STAFF)
def staff_home(request):
    return render(request, "reports/staff_home.html")
