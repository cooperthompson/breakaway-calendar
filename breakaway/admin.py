from django.contrib import admin
from breakaway.models import *


class TeamInline(admin.TabularInline):
    model = Team
    fk_name = 'league'


class LeagueAdmin(admin.ModelAdmin):
    inlines = [
        TeamInline
    ]


class TeamAdmin(admin.ModelAdmin):
    pass


class GameAdmin(admin.ModelAdmin):
    pass


admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Game, GameAdmin)