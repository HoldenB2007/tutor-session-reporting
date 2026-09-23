import datetime

from django import forms
from django.contrib.auth.models import User

from accounts.models import Role

from .queries import REPORT_KINDS, _month_end


class ReportForm(forms.Form):
    kind = forms.ChoiceField(choices=REPORT_KINDS, label="Report")
    tutor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role=Role.TUTOR).order_by("last_name"), required=False
    )
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role=Role.STUDENT).order_by("last_name"), required=False
    )
    period = forms.ChoiceField(
        choices=[("month", "Single month"), ("range", "Date range")], widget=forms.RadioSelect, initial="month"
    )
    month = forms.CharField(required=False, widget=forms.TextInput(attrs={"type": "month"}))
    start = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="From")
    end = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="To")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["month"].initial = datetime.date.today().strftime("%Y-%m")
        self.fields["tutor"].label_from_instance = lambda u: u.get_full_name()
        self.fields["student"].label_from_instance = lambda u: u.get_full_name()

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        if kind == "tutor" and not cleaned.get("tutor"):
            self.add_error("tutor", "Choose a tutor.")
        if kind == "student" and not cleaned.get("student"):
            self.add_error("student", "Choose a student.")

        if cleaned.get("period") == "month":
            try:
                first = datetime.datetime.strptime(cleaned.get("month") or "", "%Y-%m").date()
            except ValueError:
                self.add_error("month", "Pick a month.")
                return cleaned
            cleaned["start"], cleaned["end"] = first, _month_end(first)
        else:
            start, end = cleaned.get("start"), cleaned.get("end")
            if not start or not end:
                self.add_error("start", "Enter both dates.")
            elif start > end:
                self.add_error("end", "End must be after start.")
        return cleaned


class SubscriptionForm(forms.ModelForm):
    class Meta:
        from .models import ReportSubscription

        model = ReportSubscription
        fields = ["email", "kind"]
