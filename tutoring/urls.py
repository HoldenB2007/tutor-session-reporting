from django.urls import path

from . import views

urlpatterns = [
    path("tutor/", views.tutor_home, name="tutor_home"),
    path("tutor/grid/", views.tutor_grid, name="tutor_grid"),
    path("tutor/assignments/<int:pk>/", views.assignment_menu, name="assignment_menu"),
    path("tutor/assignments/<int:pk>/history/", views.session_history, name="session_history"),
    path("tutor/assignments/<int:pk>/log-session/", views.log_session, name="log_session"),
    path("tutor/assignments/<int:pk>/goals/", views.update_goals, name="update_goals"),
    path("tutor/assignments/<int:pk>/schedule/", views.update_schedule, name="update_schedule"),
    path("tutor/assignments/<int:pk>/end/", views.end_tutoring, name="end_tutoring"),
    path("student/", views.student_home, name="student_home"),
]
