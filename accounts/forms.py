from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image", "pronouns"]
        labels = {"image": "Profile photo", "pronouns": "Pronouns"}
        widgets = {"pronouns": forms.TextInput(attrs={"placeholder": "e.g. she/her, they/them"})}
