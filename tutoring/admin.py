from django.contrib import admin

from .models import Assignment, Goal, GoalAchievement, Session


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ("date", "hours", "absence", "note")


class GoalAchievementInline(admin.TabularInline):
    model = GoalAchievement
    extra = 0


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("student", "tutor", "subject", "site", "started_on", "ended_on")
    list_filter = ("tutor", "ended_on")
    search_fields = ("student__first_name", "student__last_name", "tutor__first_name", "tutor__last_name")
    autocomplete_fields = ("tutor", "student")
    inlines = [SessionInline, GoalAchievementInline]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("date", "assignment", "hours", "absence")
    list_filter = ("absence", "assignment__tutor")
    date_hierarchy = "date"


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("category", "order", "label", "federally_reported")
    list_filter = ("category", "federally_reported")
    list_editable = ("order", "label", "federally_reported")


@admin.register(GoalAchievement)
class GoalAchievementAdmin(admin.ModelAdmin):
    list_display = ("achieved_on", "assignment", "goal")
    list_filter = ("goal__category",)
    date_hierarchy = "achieved_on"
