from django.conf import settings
from django.db import models
from django.db.models import Q

from .utils import fiscal_year_for


class Assignment(models.Model):
    """
    A tutor–student pairing. This is what one paper form represents.
    A student may have several assignments (different tutors for different subjects).
    """

    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tutor_assignments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="student_assignments")
    subject = models.CharField(max_length=100, blank=True, help_text="e.g. ESL, GED math")
    site = models.CharField(max_length=120, blank=True, help_text="Tutoring site")
    days = models.CharField(max_length=120, blank=True, help_text="e.g. Mon & Wed")
    times = models.CharField(max_length=120, blank=True, help_text="e.g. 6:00–7:30 pm")
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    end_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["student__last_name", "student__first_name"]

    def __str__(self):
        return f"{self.tutor.get_full_name()} → {self.student.get_full_name()}"

    @property
    def is_active(self):
        return self.ended_on is None

    @property
    def fiscal_year(self):
        return fiscal_year_for(self.started_on)


class Absence(models.TextChoices):
    TUTOR_ABSENT = "TA", "Tutor absent"
    STUDENT_ABSENT = "SA", "Student absent"
    HOLIDAY = "H", "Holiday"


class Session(models.Model):
    """One meeting (or missed meeting). Exactly one of `hours` or `absence` is set."""

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField()
    hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    absence = models.CharField(max_length=2, choices=Absence.choices, blank=True, default="")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(hours__isnull=False, hours__gt=0, absence="") | Q(hours__isnull=True) & ~Q(absence="")),
                name="session_hours_xor_absence",
            ),
        ]

    def __str__(self):
        what = f"{self.hours}h" if self.hours is not None else self.get_absence_display()
        return f"{self.assignment} on {self.date}: {what}"

    @property
    def is_absence(self):
        return bool(self.absence)


class GoalCategory(models.TextChoices):
    ECONOMIC = "A", "A. Economic"
    EDUCATIONAL = "B", "B. Educational"
    FAMILY = "C", "C. Family"
    SOCIETAL = "D", "D. Societal/Community"
    OTHER = "E", "E. Other"


class Goal(models.Model):
    """A fixed achievement from the paper form. Edited only by staff in the admin."""

    category = models.CharField(max_length=1, choices=GoalCategory.choices)
    label = models.CharField(max_length=120)
    federally_reported = models.BooleanField(default=False, help_text="Starred on the paper form")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["category", "order"]
        unique_together = [("category", "label")]

    def __str__(self):
        star = "*" if self.federally_reported else ""
        return f"{self.get_category_display()} — {star}{self.label}"


class GoalAchievement(models.Model):
    """A goal checked off for a particular tutor–student assignment."""

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="achievements")
    goal = models.ForeignKey(Goal, on_delete=models.PROTECT, related_name="achievements")
    achieved_on = models.DateField()

    class Meta:
        unique_together = [("assignment", "goal")]
        ordering = ["achieved_on"]

    def __str__(self):
        return f"{self.assignment.student.get_full_name()}: {self.goal.label} ({self.achieved_on})"
