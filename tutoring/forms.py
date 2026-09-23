import datetime

from django import forms

from .models import Absence, Assignment, Goal, Session


class SessionForm(forms.ModelForm):
    """Date is required; then either hours tutored or an absence — never both, never neither."""

    class Meta:
        model = Session
        fields = ["date", "hours", "absence", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "max": datetime.date.today().isoformat()}),
            "hours": forms.NumberInput(attrs={"step": "0.25", "min": "0.25", "placeholder": "e.g. 1.5"}),
            "absence": forms.RadioSelect(choices=[("", "No — we met")] + list(Absence.choices)),
        }
        labels = {"hours": "Hours tutored", "absence": "Absence?", "note": "Note (optional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = datetime.date.today()
        self.fields["absence"].required = False

    def clean(self):
        cleaned = super().clean()
        hours, absence = cleaned.get("hours"), cleaned.get("absence")
        if absence and hours:
            raise forms.ValidationError("Enter hours or mark an absence, not both.")
        if not absence and not hours:
            raise forms.ValidationError("Enter the hours tutored, or mark an absence.")
        return cleaned


class GoalsForm(forms.Form):
    goals = forms.ModelMultipleChoiceField(
        queryset=Goal.objects.all(), widget=forms.CheckboxSelectMultiple, required=False
    )

    def __init__(self, assignment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment
        self.fields["goals"].initial = assignment.achievements.values_list("goal_id", flat=True)

    def save(self):
        """Add achievements for newly checked goals; remove any that were unchecked."""
        chosen = set(self.cleaned_data["goals"].values_list("pk", flat=True))
        existing = set(self.assignment.achievements.values_list("goal_id", flat=True))
        self.assignment.achievements.filter(goal_id__in=existing - chosen).delete()
        today = datetime.date.today()
        for goal_id in chosen - existing:
            self.assignment.achievements.create(goal_id=goal_id, achieved_on=today)


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["site", "days", "times"]


class EndForm(forms.ModelForm):
    confirm = forms.BooleanField(label="I understand this ends tutoring for this student and notifies the office.")

    class Meta:
        model = Assignment
        fields = ["ended_on", "end_reason"]
        widgets = {
            "ended_on": forms.DateInput(attrs={"type": "date"}),
            "end_reason": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {"ended_on": "Last day", "end_reason": "Reason"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ended_on"].initial = datetime.date.today()
        self.fields["ended_on"].required = True
