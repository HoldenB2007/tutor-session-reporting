"""Seed the fixed goals list from LVAEP's Student Monthly Attendance & Achievement Form."""

from django.db import migrations

# (category, order, label, federally_reported)  — starred items on the paper form are federally reported.
GOALS = [
    ("A", 1, "Enter employment", True),
    ("A", 2, "Retain employment", True),
    ("A", 3, "Leave public assistance", False),
    ("B", 1, "Achieve work-based project learner goal", False),
    ("B", 2, "Enter occupational skills training program", True),
    ("B", 3, "Enter postsecondary education", True),
    ("B", 4, "Obtain high school diploma", True),
    ("C", 1, "Help more frequently with school", False),
    ("C", 2, "Increase contact with child(ren)'s teachers", False),
    ("C", 3, "More involvement in child(ren)'s school activities", False),
    ("C", 4, "Purchase books or magazines", False),
    ("C", 5, "Read to child(ren)", False),
    ("C", 6, "Visit the library (with/for child(ren))", False),
    ("D", 1, "Obtain citizenship", True),
    ("D", 2, "Achieve civics skills", False),
    ("D", 3, "Increase involvement in community activities", False),
    ("D", 4, "Vote or register to vote", False),
]


def seed(apps, schema_editor):
    Goal = apps.get_model("tutoring", "Goal")
    for category, order, label, federal in GOALS:
        Goal.objects.get_or_create(
            category=category, label=label, defaults={"order": order, "federally_reported": federal}
        )


def unseed(apps, schema_editor):
    Goal = apps.get_model("tutoring", "Goal")
    Goal.objects.filter(label__in=[g[2] for g in GOALS]).delete()


class Migration(migrations.Migration):
    dependencies = [("tutoring", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
