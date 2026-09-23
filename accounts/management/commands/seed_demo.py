"""
Create demo accounts and sample tutoring data so the app can be reviewed unattended.

Idempotent: re-running updates passwords/profiles and leaves existing sessions alone.
"""

import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.demo import DEMO_ACCOUNTS, DEMO_PASSWORD
from accounts.models import Profile, Role
from tutoring.models import Absence, Assignment, Goal, GoalAchievement, Session

# Weekly schedule per assignment: (weekday numbers, hours per session)
ASSIGNMENTS = [
    # tutor, student, subject, site, days, times, weekdays, hours
    ("tutor.maria", "student.ana", "ESL", "Bloomfield Public Library", "Mon & Wed", "6:00–7:30 pm", (0, 2), "1.5"),
    ("tutor.maria", "student.wei", "GED math", "Bloomfield Public Library", "Tue", "10:00–12:00", (1,), "2"),
    ("tutor.james", "student.wei", "ESL conversation", "Online (Zoom)", "Thu", "7:00–8:00 pm", (3,), "1"),
    ("tutor.james", "student.samuel", "Citizenship prep", "Nutley Public Library", "Sat", "9:00–11:00 am", (5,), "2"),
    ("tutor.james", "student.fatima", "ESL", "Bloomfield Public Library", "Mon", "4:00–5:00 pm", (0,), "1"),
]

# The Fatima assignment ended — demonstrates the "stopped" state.
ENDED = {"student.fatima": ("Moved out of the area", 21)}  # end N days ago

ACHIEVEMENTS = [
    ("student.ana", "tutor.maria", "Read to child(ren)", 30),
    ("student.ana", "tutor.maria", "Visit the library (with/for child(ren))", 12),
    ("student.wei", "tutor.maria", "Enter employment", 5),
    ("student.samuel", "tutor.james", "Achieve civics skills", 18),
]


class Command(BaseCommand):
    help = "Seed demo accounts, assignments, sessions, and achievements."

    @transaction.atomic
    def handle(self, *args, **options):
        users = {}
        for spec in DEMO_ACCOUNTS:
            user, _ = User.objects.get_or_create(username=spec["username"])
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.email = f"{spec['username']}@example.org"
            user.is_staff = spec["role"] == Role.STAFF  # staff get Django admin access
            user.set_password(DEMO_PASSWORD)
            user.save()
            Profile.objects.update_or_create(user=user, defaults={"role": spec["role"]})
            users[spec["username"]] = user
        self.stdout.write(f"{len(users)} demo users ready")

        today = datetime.date.today()
        start = today - datetime.timedelta(days=75)  # ~2.5 months of history

        created_sessions = 0
        for tutor, student, subject, site, days, times, weekdays, hours in ASSIGNMENTS:
            assignment, created = Assignment.objects.get_or_create(
                tutor=users[tutor],
                student=users[student],
                subject=subject,
                defaults={"site": site, "days": days, "times": times, "started_on": start},
            )
            if student in ENDED:
                reason, days_ago = ENDED[student]
                assignment.ended_on = today - datetime.timedelta(days=days_ago)
                assignment.end_reason = reason
                assignment.save()

            if not created:
                continue  # keep existing session history intact on re-runs

            last_day = assignment.ended_on or today
            day = start
            i = 0
            while day <= last_day:
                if day.weekday() in weekdays:
                    i += 1
                    # Sprinkle in absences so reports have something to show.
                    if i % 7 == 0:
                        Session.objects.create(assignment=assignment, date=day, absence=Absence.STUDENT_ABSENT)
                    elif i % 11 == 0:
                        Session.objects.create(assignment=assignment, date=day, absence=Absence.TUTOR_ABSENT)
                    else:
                        Session.objects.create(assignment=assignment, date=day, hours=Decimal(hours))
                    created_sessions += 1
                day += datetime.timedelta(days=1)
        self.stdout.write(f"{created_sessions} sessions created")

        for student, tutor, goal_label, days_ago in ACHIEVEMENTS:
            assignment = Assignment.objects.filter(student=users[student], tutor=users[tutor]).first()
            goal = Goal.objects.get(label=goal_label)
            GoalAchievement.objects.get_or_create(
                assignment=assignment, goal=goal, defaults={"achieved_on": today - datetime.timedelta(days=days_ago)}
            )
        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
