from django.contrib import admin
from django.core import urlresolvers
from breakaway.models import *


class LeagueInline(admin.TabularInline):
    model = League
    fk_name = 'season'


class SeasonAdmin(admin.ModelAdmin):
    inlines = [
        LeagueInline
    ]


class HomeGameInline(admin.TabularInline):
    model = Game
    fk_name = 'home_team'
    ordering = ('time',)


class AwayGameInline(admin.TabularInline):
    model = Game
    fk_name = 'away_team'
    ordering = ('time',)


class TeamInline(admin.TabularInline):
    model = Team
    fk_name = 'league'
    ordering = ('number', )


class LeagueAdmin(admin.ModelAdmin):
    inlines = [
        TeamInline
    ]


class TeamAdmin(admin.ModelAdmin):
    inlines = [
        HomeGameInline,
        AwayGameInline
    ]
    list_filter = ['league']


class GameAdmin(admin.ModelAdmin):
    list_filter = ['home_team__league']


admin.site.register(Season, SeasonAdmin)
admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Game, GameAdmin)