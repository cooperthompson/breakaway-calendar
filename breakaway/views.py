from django.http import HttpResponse
from django.template import RequestContext, loader
from breakaway.models import *


def home(request):
    leagues = League.objects.all()
    leagues.prefetch_related('teams')

    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'leagues': leagues,
    })
    return HttpResponse(template.render(context))


def team(request, team_id):
    leagues = League.objects.all()
    leagues.prefetch_related('teams')

    this_team = Team.objects.get(id=team_id)
    home_games = Game.objects.filter(home_team=this_team)
    away_games = Game.objects.filter(away_team=this_team)

    games = home_games | away_games

    template = loader.get_template('team.html')
    context = RequestContext(request, {
        'leagues': leagues,
        'games': games,
    })
    return HttpResponse(template.render(context))