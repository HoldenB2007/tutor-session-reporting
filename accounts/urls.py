from django.contrib.auth.views import LogoutView
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", views.profile_edit, name="profile"),
    re_path(r"^media/(?P<path>.*)$", views.media, name="media"),
]
