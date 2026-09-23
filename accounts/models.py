from django.conf import settings
from django.db import models


class Role(models.TextChoices):
    STUDENT = "student", "Student"
    TUTOR = "tutor", "Tutor"
    STAFF = "staff", "Staff"


class Profile(models.Model):
    """Per-user role and display details. Every user has exactly one Profile."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=Role.choices)
    pronouns = models.CharField(max_length=40, blank=True)
    image = models.ImageField(upload_to="profiles/", blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_tutor(self):
        return self.role == Role.TUTOR

    @property
    def is_staff_role(self):
        return self.role == Role.STAFF
