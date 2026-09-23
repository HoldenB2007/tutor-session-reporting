from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import redirect

from .demo import DEMO_ACCOUNTS, DEMO_PASSWORD
from .models import Role

ROLE_HOME = {
    Role.STUDENT: "student_home",
    Role.TUTOR: "tutor_home",
    Role.STAFF: "staff_home",
}


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.SHOW_DEMO_CREDENTIALS:
            context["demo_accounts"] = DEMO_ACCOUNTS
            context["demo_password"] = DEMO_PASSWORD
        return context


@login_required
def home(request):
    """Send each role to its own landing page."""
    profile = getattr(request.user, "profile", None)
    if profile is None:
        # A user without a Profile (e.g. a raw superuser) can only use the admin.
        return redirect("admin:index")
    return redirect(ROLE_HOME[profile.role])
