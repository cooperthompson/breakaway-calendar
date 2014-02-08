from django.http import HttpResponse
from django.template import RequestContext, loader
from breakaway.models import *
from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
import pdb
import shortuuid


def home(request):
    leagues = League.objects.filter(is_active=True)
    leagues.prefetch_related('teams')

    today = date.today()
    tomorrow = today + timedelta(days=1)
    games = Game.objects.filter(time__gte=today)
    games = games.filter(time__lt=tomorrow)
    games = games.order_by("time", "field")

    template = loader.get_template('home.html')
    context = RequestContext(request, {
        'leagues': leagues,
        'games': games,
    })
    return HttpResponse(template.render(context))


def team(request, team_id):
    leagues = League.objects.filter(is_active=True)
    leagues.prefetch_related('teams')

    this_team = Team.objects.get(id=team_id)
    home_games = Game.objects.filter(home_team=this_team)
    away_games = Game.objects.filter(away_team=this_team)

    games = home_games | away_games
    games = games.order_by("time", "field")

    template = loader.get_template('team.html')
    context = RequestContext(request, {
        'team': this_team,
        'leagues': leagues,
        'games': games,
    })
    return HttpResponse(template.render(context))


def league(request, league_id):
    leagues = League.objects.filter(is_active=True)
    leagues.prefetch_related('teams')

    this_league = League.objects.get(id=league_id)

    template = loader.get_template('league.html')
    context = RequestContext(request, {
        'leagues': leagues,
        'league': this_league,
    })
    return HttpResponse(template.render(context))


def ics(request, team_id=None, team_name=None):

    if team_id:
        this_team = Team.objects.get(id=team_id)
    elif team_name:
        this_team = Team.objects.get(name=team_name)

    home_games = Game.objects.filter(home_team=this_team)
    away_games = Game.objects.filter(away_team=this_team)

    games = home_games | away_games
    games = games.order_by("time", "field")

    cal = Calendar()
    cal.add('prodid', '-//Breakway Schedules//mxm.dk//')
    cal.add('version', '2.0')

    now_dt = datetime.now()
    now_string = "%04d%02d%02dT%02d%02d%02d" % (
        now_dt.year,
        now_dt.month,
        now_dt.day,
        now_dt.hour,
        now_dt.minute,
        now_dt.second
    )

    for game in games:
        event = Event()
        try:
            event.add('summary', '%s vs. %s' % (game.home_team, game.away_team))
        except Exception as e:
            print e
            pdb.set_trace()
        event.add('dtstart', game.time)
        event.add('dtend', game.time + timedelta(hours=1))
        event.add('dtstamp', datetime.now())
        event.add('location', "BreakAway Field %s" % game.field)
        event['uid'] = '%s/%s@breakawaysports.com' % (now_string, shortuuid.uuid())
        event.add('priority', 5)
        cal.add_component(event)

    return HttpResponse(cal.to_ical(), content_type='text/calendar')


def master_ics(request):
    cal = Calendar()
    cal.add('prodid', '-//Breakway Schedules//mxm.dk//')
    cal.add('version', '2.0')

    now_dt = datetime.now()
    now_string = "%04d%02d%02dT%02d%02d%02d" % (
        now_dt.year,
        now_dt.month,
        now_dt.day,
        now_dt.hour,
        now_dt.minute,
        now_dt.second
    )
    games = Game.objects.filter(home_team__league__is_active=True)
    games = games.order_by("time", "field")
    for game in games:
        event = Event()
        try:
            event.add('summary', '%s vs. %s' % (game.home_team, game.away_team))
        except Exception as e:
            print e
            pdb.set_trace()
        event.add('dtstart', game.time)
        event.add('dtend', game.time + timedelta(hours=1))
        event.add('dtstamp', datetime.now())
        event.add('location', "BreakAway Field %s" % game.field)
        event['uid'] = '%s/%s@breakawaysports.com' % (now_string, shortuuid.uuid())
        event.add('priority', 5)
        cal.add_component(event)

    return HttpResponse(cal.to_ical(), content_type='text/calendar')