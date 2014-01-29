#-------------------------------------------------------------------------------
# Name:        breakaway-parser
# Purpose:     Parse Breakaway PDF into ICS file
#
# Author:      cthompso
#
# Created:     12/06/2013
# Copyright:   (c) cthompso 2013
# Licence:     MIT
#-------------------------------------------------------------------------------

import pdb,tempfile,subprocess,re
from optparse import OptionParser
from icalendar import Calendar, Event
import pytz
from datetime import datetime, timedelta, date
import time

def main():
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")

    (options, args) = parser.parse_args()

    teams = get_teams(options.filename)
    games = get_games(options.filename)

    for key,team in teams.items():
        create_ics(team, games, teams)

def create_ics(team, games, teams):
    cal = Calendar()
    cal.add('prodid', '-//Breakway Schedules//mxm.dk//')
    cal.add('version', '2.0')

    for game in games:
        if team.id == game.away_team or team.id == game.home_team:
            event = Event()
            try:
                event.add('summary', '%s vs. %s' % (teams[game.home_team], teams[game.away_team]))
            except Exception as e:
                pdb.set_trace()
            event.add('dtstart', game.datetime)
            event.add('dtend',   game.datetime + timedelta(hours=1))
            event.add('dtstamp', datetime.now())
            event.add('location', "BreakAway Field %s" % (game.field))
            event['uid'] = '20050115T101010/27346262376@mxm.dk'
            event.add('priority', 5)
            cal.add_component(event)

    file = open('ics/%s - %s.ics' % (team.id, team.name), 'wb')
    file.write(cal.to_ical())
    file.close()


def get_games(filename):
    # Use the non-layout version to parse out the teams.
    with open(filename, 'r') as pdf_file:
        text_file = ConvertPDFToText(pdf_file,0)

    games = []
    mode = "start"
    week = ""
    game_date = ""

    today = datetime.now()

    while True:
        line = text_file.readline()
        if not line: break #EOF

        if line.strip() == "TEAM (COLOR)":
            mode = "team"
        if line.strip() == "GOOD LUCK & HAVE FUN!":
            mode = "team-complete"
        if line.strip() == "WEEK 1":
            mode = "sched"
        if line.strip() == "IMPORTANT EVERYONE READ!":
            mode = "sched-complete"

        home_team = 0
        away_team = 0
        game_time = ""
        field = ""

        try:
            match = re.match("WEEK (\d+)",line)
            if mode == "sched" and match:
                week = match.group(1)

            match = re.match("(\w+)\.(\w+)\.\s+(\d+)",line)
            if mode == "sched" and match:
                day_of_week = match.group(1)
                month_of_year = match.group(2)
                day_of_month = match.group(3)
                month_dt = datetime.strptime(month_of_year, '%b') # convert string format to month number

            match = re.match("(\d+)-(\d+) (\d+\:\d{2})(\d?)",line)
            if mode == "sched" and match:
                home_team = int(match.group(1))
                away_team = int(match.group(2))
                game_time = match.group(3)
                field = match.group(4)

            # catch the case where pdftotext didn't get the splitting right
            match_time = re.match("(\d+\:\d{2})(\d?)$",line)
            match_mtch = re.match("(\d+)-(\d+)$",line)
            if mode == "sched" and (match_time or match_mtch):
                line2 = text_file.readline()
                if not line2: break #EOF

                if match_time:
                    match_mtch = re.match("(\d+)-(\d+)$",line2)
                elif match_mtch:
                    match_time = re.match("(\d+\:\d{2})(\d?)$",line2)

                game_time = match_time.group(1)
                field = match_time.group(2)

                home_team = int(match_mtch.group(1))
                away_team = int(match_mtch.group(2))

        except Exception as e:
            print "%s - %s" % (e,line)

        if mode =="sched" and home_team and away_team:
            try:
                date_string = "%02d/%s/%s %s PM" % (int(day_of_month), month_dt.month,  today.year, game_time)
                game_datetime = datetime.strptime(date_string, '%d/%m/%Y %I:%M %p')
            except Exception as e:
                pdb.set_trace()

            if not field: field = "1" # default to field 1
            game = Game(home_team, away_team, game_datetime, field)
            games.append(game)


    for game in games:
        print game

    return games


def get_teams(filename):
    # Use the layout version to parse out the teams.
    with open(filename, 'r') as pdf_file:
        text_file = ConvertPDFToText(pdf_file,1)

    teams = {}
    mode = "start"

    for line in text_file:
        if line.strip() == "TEAM (COLOR)":
            mode = "team"
        if line.strip() == "GOOD LUCK & HAVE FUN!":
            mode = "team-complete"
        if line.strip() == "WEEK 1":
            mode = "sched"
        if line.strip() == "IMPORTANT EVERYONE READ!":
            mode = "sched-complete"

        if mode == "team" and re.match("\d+.*",line.strip()):
            team_handler(line,teams)

    for team_id,team in teams.items():
        print team

    return teams

def team_handler(line, teams):
    match = match = re.match("\s*(\d+)\.?\s+(.*)\s+(\d+)\.\s+(.*)",line)
    if match is None:
        match = re.match("\s*(\d+)\.?\s+(.*)$",line)

    if match is None:
        print line

    try:
        team1_id = int(match.group(1))
        team1_nm = match.group(2)
        team1 = Team(team1_id, team1_nm)
        teams[team1_id] = team1
    except Exception as e:
        print "Warning: %s - %s" % (e,line)
    try:
        team2_id = int(match.group(3))
        team2_nm = match.group(4)
        team2 = Team(team2_id, team2_nm)
        teams[team2_id] = team2
    except Exception as e:
        print "Warning: %s - %s" % (e,line)

class Team:
    def __init__(self, id):
        self._schedule = []
        self._id = id

    def __init__(self, id, name):
        self._schedule = []
        self._id = id
        self.name = unicode(name.strip(), errors='ignore')

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,value):
        self._name = value

    @property
    def schedule(self):
        return self._schedule

    def add_game(self,game):
        self._schedule.append(game)

    def __unicode__(self):
        return "%s - %s" % (self._id, self._name)

    def __str__(self):
        return self.__unicode__()

class Game:
    def __init__(self, home_team, away_team, datetime, field):
        self._home_team = home_team
        self._away_team = away_team
        self._datetime = datetime
        self._field = field

    @property
    def home_team(self):
        return self._home_team

    @property
    def away_team(self):
        return self._away_team

    @property
    def datetime(self):
        return self._datetime

    @property
    def field(self):
        return self._field

    def __unicode__(self):
        return "%s [%02s vs. %02s] [Field %s]" % (self._datetime.isoformat(' '), self._home_team, self._away_team, self._field)

    def __str__(self):
        return self.__unicode__()

def ConvertPDFToText(currentPDF,layout):
    pdfData = currentPDF.read()

    tf = tempfile.NamedTemporaryFile()
    tf.write(pdfData)
    tf.seek(0)

    outputTf = tempfile.NamedTemporaryFile()

    if (len(pdfData) > 0) :
        if layout:
            out, err = subprocess.Popen(["pdftotext", "-layout", tf.name, outputTf.name ]).communicate()
        else:
            out, err = subprocess.Popen(["pdftotext", tf.name, outputTf.name ]).communicate()
        return outputTf
    else :
        return None


if __name__ == '__main__':
    main()
