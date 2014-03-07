from django.contrib import admin
from breakaway.models import *


class LeagueInline(admin.TabularInline):
    model = League
    fk_name = 'season'


class TeamInline(admin.TabularInline):
    model = Team
    fk_name = 'league'
    ordering = ('number', )
    fields = ['number', 'name', 'color']


class HomeGameInline(admin.TabularInline):
    model = Game
    fk_name = 'home_team'
    ordering = ('time',)


class AwayGameInline(admin.TabularInline):
    model = Game
    fk_name = 'away_team'
    ordering = ('time',)


class LeagueAdmin(admin.ModelAdmin):
    inlines = [TeamInline]
    fields = ['name', 'is_active']
    readonly_fields = ['key']
    list_display = ['__unicode__', 'name', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']
    list_editable = ['name', 'is_active']


class TeamAdmin(admin.ModelAdmin):
    inlines = [HomeGameInline, AwayGameInline]
    list_filter = ['league']
    list_display = ['number', 'name', 'color', 'league']
    list_display_links = ['name']
    search_fields = ['number', 'name']


class GameAdmin(admin.ModelAdmin):
    fields = ['league', 'home_team', 'away_team', 'time', 'field']
    list_display = ['id', '__unicode__',
                    'home_team',
                    'away_team',
                    'time',
                    'field']
    list_display_links = ['__unicode__']
    list_filter = ['league',
                   'home_team',
                   'away_team']
    search_fields = ['home_team__name',
                     'away_team__name']


admin.site.register(League, LeagueAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Game, GameAdmin)