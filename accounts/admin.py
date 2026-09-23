from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


class UserAdmin(DjangoUserAdmin):
    """Default user admin plus the Profile inline so staff set a role when creating an account."""

    inlines = [ProfileInline]
    list_display = ("username", "first_name", "last_name", "email", "role")
    list_filter = ("profile__role", "is_active")
    search_fields = ("username", "first_name", "last_name", "email")

    @admin.display(description="Role")
    def role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, "profile") else "—"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "pronouns")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
