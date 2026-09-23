from django.urls import path

from . import views

urlpatterns = [
    path("tutor/", views.tutor_home, name="tutor_home"),
    path("student/", views.student_home, name="student_home"),
]
