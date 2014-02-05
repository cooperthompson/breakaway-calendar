from django.contrib import admin
from breakaway.models import *


class LeagueInline(admin.TabularInline):
    model = League
    fk_name = 'season'


class SeasonAdmin(admin.ModelAdmin):
    inlines = [
        LeagueInline
    ]


class TeamInline(admin.TabularInline):
    model = Team
    fk_name = 'league'
    ordering = ('number', )


class LeagueAdmin(admin.ModelAdmin):
    inlines = [
        TeamInline
    ]


class HomeGameInline(admin.TabularInline):
    model = Game
    fk_name = 'home_team'
    ordering = ('time',)


class AwayGameInline(admin.TabularInline):
    model = Game
    fk_name = 'away_team'
    ordering = ('time',)


class TeamAdmin(admin.ModelAdmin):
    inlines = [
        HomeGameInline,
        AwayGameInline

    ]


class GameAdmin(admin.ModelAdmin):
    pass


admin.site.register(Season, SeasonAdmin)
admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Game, GameAdmin)