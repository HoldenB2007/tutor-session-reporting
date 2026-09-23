from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import redirect, render
from django.views.static import serve

from .decorators import role_required
from .demo import DEMO_ACCOUNTS, DEMO_PASSWORD
from .forms import ProfileForm
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


@role_required(Role.STUDENT, Role.TUTOR)
def profile_edit(request):
    """Students and tutors set a photo and pronouns. Staff is a shared account and has no profile page."""
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("home")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def media(request, path):
    """Serve uploaded files (profile photos) to logged-in users only."""
    return serve(request, path, document_root=settings.MEDIA_ROOT)
