from django.urls import path

from . import views

urlpatterns = [
    path("tutor/", views.tutor_home, name="tutor_home"),
    path("tutor/grid/", views.tutor_grid, name="tutor_grid"),
    path("student/", views.student_home, name="student_home"),
]
