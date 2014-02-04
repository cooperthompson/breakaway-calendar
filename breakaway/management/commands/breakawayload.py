import pdb
import re
import os
import shlex
import tempfile
import shortuuid
import urllib2
import subprocess
from datetime import datetime, timedelta, date
from django.core.management.base import BaseCommand
from icalendar import Calendar, Event
from breakaway.models import *


class Command(BaseCommand):
    args = '<pdf_file pdf_file ...>'
    help = 'Import the BreakAway PDF schedule into the Django model'

    def __init__(self):
        super(Command, self).__init__()
        self.season = ""
        self.league = ""

    def handle(self, *args, **options):
        pdf_files = self.get_pdf_files()

        for pdf_filename in pdf_files:
            self.load_file(pdf_filename)

    def get_pdf_files(self):
        pdf_files = []
        response = urllib2.urlopen('http://breakawaysports.com/current-league.php')
        html = response.read()
        matches = re.findall(".*href=\"(.*\.pdf)\".*", html)

        self.season = Season(name="current")
        self.season.save()

        for match in matches:
            pdf_files.append("http://breakawaysports.com%s" % match)

        return pdf_files

    def load_file(self, pdf_filename):
        self.stdout.write('Loading %s' % pdf_filename)
        match = re.match(".*\.(.*).pdf", pdf_filename)
        league_name = match.group(1)

        self.league = League(name=league_name,
                             season=self.season)
        self.league.save()

        # just some test stuff for windows
        if os.name == "nt" and False:  # windows
            # on windows, use pre-processed text files for testing, since
            # pdftotext doesn't do the same layouting as it does on linux
            text_layout_filename = r'C:\Users\cooper\Desktop\142650-857601.adultcoedw21314-layout.txt'
            text_filename = r'C:\Users\cooper\Desktop\142650-857601.adultcoedw21314.txt'

            with open(text_layout_filename, 'r') as text_file:
                self.get_teams(text_file)

            with open(text_filename, 'r') as text_file:
                self.get_games_non_layout(text_file)

        pdf_file = urllib2.urlopen(pdf_filename)
        local_pdf_file = tempfile.NamedTemporaryFile(delete=False)
        local_pdf_file.write(pdf_file.read())
        local_pdf_file.close()

        with open(local_pdf_file.name, 'r') as pdf_file:
            text_file = self.ConvertPDFToText(pdf_file, 0)  # non-layout version
            self.get_teams(text_file)

        with open(local_pdf_file.name, 'r') as pdf_file:
            text_file = self.ConvertPDFToText(pdf_file, 1)  # layout version
            self.get_games_non_layout(text_file)

        self.stdout.write('Successfully imported "%s"' % pdf_filename)

    def ConvertPDFToText(self, pdf_file, layout):
        """

        @param pdf_file: open PDF file to convert
        @param layout: boolean indicator if the PDF should be parsed into a
            layout or non-layout text document
        @return: text version of the PDF
        """
        outputTf = tempfile.NamedTemporaryFile(delete=False)

        if layout:
            cmd = "pdftotext -layout '%s' '%s'" % (pdf_file.name, outputTf.name)
            proc = subprocess.Popen(shlex.split(cmd))
            out, err = proc.communicate()
        else:
            cmd = "pdftotext '%s' '%s'" % (pdf_file.name, outputTf.name)
            proc = subprocess.Popen(shlex.split(cmd))
            out, err = proc.communicate()

        if err:
            self.stdout.write("ERROR: %s" % err)

        return outputTf

    def get_games(self, text_file):
        mode = "start"

        dates = []
        while True:
            line = text_file.readline()
            if not line:
                break  # EOF

            if line.startswith("WEEK 1"):
                mode = "sched"
            if line.startswith("IMPORTANT EVERYONE READ!"):
                mode = "sched-complete"

            if mode != "sched":
                continue

            lex_line = shlex.split(line)
            if not lex_line:
                continue

            match = re.match("((\w{2,3})\.(\w{3}))+", lex_line[0])
            if match:
                date_line = lex_line
                dates = []
                self.stdout.write("dateline: %s" % date_line)

                for day, dt in self.group(date_line, 2):
                    date_string = "%s %s" % (day, dt)
                    game_date = self.parse_pdf_datetime(date_string)
                    self.stdout.write(game_date.strftime("%A, %B %d,  %Y"))
                    dates.append(game_date)

            match = re.match("\d+-\d+.*", lex_line[0])
            if match:
                game_line = self.fix_line(lex_line)
                self.stdout.write("gameline: %s" % game_line)
                date_index = 0

                for game, time in group(game_line, 2):
                    game_date = dates[date_index]
                    date_index += 1
                    self.save_game(game, time, game_date)

    def get_games_non_layout(self, text_file):
        mode = "start"
        game_date = datetime.now()

        while True:
            line = text_file.readline()
            if not line:
                break  # EOF

            if line.strip() == "TEAM (COLOR)":
                mode = "team"
            if line.strip() == "GOOD LUCK & HAVE FUN!":
                mode = "team-complete"
            if line.strip() == "WEEK 1":
                mode = "sched"
            if line.strip() == "IMPORTANT EVERYONE READ!":
                mode = "sched-complete"

            match = re.match("(\w+)\.(\w+)\.\s+(\d+)", line)
            if mode == "sched" and match:
                game_date = line

            match = re.match("(\d+)-(\d+) (\d+:\d{2})(\d?)", line)
            if mode == "sched" and match:
                home_team = Team.objects.filter(league=self.league).get(number=int(match.group(1)))
                away_team = Team.objects.filter(league=self.league).get(number=int(match.group(2)))
                game_time = match.group(3)
                field = match.group(4)
                if not field:
                    field = 1

                game_time = self.parse_pdf_datetime(game_date, game_time)
                game = Game(home_team=home_team,
                            away_team=away_team,
                            time=game_time,
                            field=field)
                print game
                game.save()

            # handle the case where pdftotext didn't get the splitting right
            match_time = re.match("(\d+:\d{2})(\d?)$", line)
            match_mtch = re.match("(\d+)-(\d+)$", line)
            if mode == "sched" and (match_time or match_mtch):
                line2 = text_file.readline()
                if not line2:
                    break  # EOF

                if match_time:
                    match_mtch = re.match("(\d+)-(\d+)$", line2)
                elif match_mtch:
                    match_time = re.match("(\d+:\d{2})(\d?)$", line2)

                home_team = Team.objects.filter(league=self.league).get(number=int(match_mtch.group(1)))
                away_team = Team.objects.filter(league=self.league).get(number=int(match_mtch.group(2)))
                game_time = match_time.group(1)
                field = match_time.group(2)
                if not field:
                    field = 1

                game_time = self.parse_pdf_datetime(game_date, game_time)

                game = Game(home_team=home_team,
                            away_team=away_team,
                            time=game_time,
                            field=field)
                print game
                game.save()

        return

    def fix_line(self, lex_line):
        fixed_line = []
        self.stdout.write("Initial line: %s" % lex_line)
        for element in lex_line:
            if re.match("\d+-\d+$", element):
                fixed_line.append(element)
            elif re.match("\d+:\d+$", element):
                fixed_line.append(element)
            else:
                match = re.match("(\d+:\d{2}2)(\d+-\d+)", element)
                try:
                    fixed_line.append(match.group(1))
                    fixed_line.append(match.group(2))
                except Exception as e:
                    pdb.set_trace()

        print "Fixed line: %s" % fixed_line
        return fixed_line

    def save_game(self, game, time, game_date):
        home_team, away_team = game.split("-")

        match = re.match("(\d+:\d{2})(\d?)$", time)
        try:
            time = match.group(1)
            field = match.group(2)
        except Exception as e:
            self.stdout.write("%s - %s" % (e, time))

        self.stdout.write("%s vs. %s at %s on %s on %s" % (home_team,
                                                           away_team,
                                                           time,
                                                           field,
                                                           game_date.strftime("%A, %B %d,  %Y")))

    @staticmethod
    def group(lst, n):
        for i in range(0, len(lst), n):
            val = lst[i:i+n]
            if len(val) == n:
                yield tuple(val)

    def parse_pdf_datetime(self, date_string, time_string):
        match_date = re.match("(\w{2,3})\.(\w{3}).*?(\d+)", date_string)
        match_time = re.match("(\d+):(\d{2})", time_string)

        if match_date and match_time:
            game_mo = match_date.group(2)
            game_dt = int(match_date.group(3))
            game_hr = int(match_time.group(1))
            game_mn = int(match_time.group(2))

            game_month = datetime.strptime(game_mo, '%b').month  # convert string format to month number
            if game_month == 12:
                game_year = 2013
            else:
                game_year = 2014

            game_hr += 12  # covert to 24 hour time.  Always assume games are in the evening..

            game_dt = int(game_dt)
            game_datetime = datetime(game_year, game_month, game_dt, game_hr, game_mn)
            #print game_datetime.strftime("%A, %B %d,  %Y  %I:%M %p")
        else:
            self.stdout.write(date_string)
            game_datetime = None
        return game_datetime

    def process_game_line_nolayout(self, lex_line):
        for index, element in enumerate(lex_line):
            match = re.match("(\w{2,3})\.(\w{3})", element)
            if match:
                game_mo = match.group(2)
                game_dt = lex_line[index+1]

                game_month = datetime.strptime(game_mo, '%b').month  # convert string format to month number
                if game_month == 12:
                    game_year = 2013
                else:
                    game_year = 2014

                game_dt = int(game_dt)
                game_datetime = date(game_year, game_month, game_dt)
                self.stdout.write(game_datetime.strftime("%A, %B %d,  %Y"))

        for game in Game.objects.all():
            print game

    def get_teams(self, text_file):
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

            if mode == "team" and re.match("\d+.*", line.strip()):
                self.team_handler(line)

        for team in Team.objects.all():
            print team

    def team_handler(self, line):
        """

        @param line: A single lien from the PDF to be parsed for team data
        """
        match = re.match("\s*(\d+)\.?\s+(.*)\s+(\d+)\.\s+(.*)", line)
        if match is None:
            match = re.match("\s*(\d+)\.?\s+(.*)$", line)

        if match is None:
            print "Unmatched: %s" % line

        self.save_team(match.group(1), match.group(2))

        # mose lines have two teams per line
        if len(match.groups()) > 2:
            self.save_team(match.group(3), match.group(4))

    def save_team(self, team_id, team_name):
        team_name = team_name.rstrip()
        match = re.match("(.*)\((.*)\)", team_name)
        if match:
            team_name = match.group(1).strip()
            team_color = match.group(2).strip()
            try:
                team = Team(number=int(team_id),
                            name=team_name,
                            color=team_color,
                            league=self.league)
                team.save()
            except Exception as e:
                self.stdout.write("[%s] - %s (%s)" % (team_id, team_name, team_color))
        else:
            self.stderr.write("No name/color found.")

    @staticmethod
    def create_ics(team):
        """

        @param team:  The team for which we should build an ICS
        """
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

        for game in Game.objects.all():
            if team.id == game.away_team or team.id == game.home_team:
                event = Event()
                try:
                    event.add('summary', '%s vs. %s' % (game.home_team, game.away_team))
                except Exception as e:
                    print e
                    pdb.set_trace()
                event.add('dtstart', game.datetime)
                event.add('dtend', game.datetime + timedelta(hours=1))
                event.add('dtstamp', datetime.now())
                event.add('location', "BreakAway Field %s" % game.field)
                event['uid'] = '%s/%s@breakawaysports.com' % (now_string, shortuuid.uuid())
                event.add('priority', 5)
                cal.add_component(event)

        ics_file = open('ics/%s - %s.ics' % (team.id, team.name), 'wb')
        ics_file.write(cal.to_ical())
        ics_file.close()

    @staticmethod
    def create_master_ics():
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

        for game in Game.objects.all():
            event = Event()
            try:
                event.add('summary', '%s vs. %s' % (game.home_team, game.away_team))
            except Exception as e:
                print e
                pdb.set_trace()
            event.add('dtstart', game.datetime)
            event.add('dtend', game.datetime + timedelta(hours=1))
            event.add('dtstamp', datetime.now())
            event.add('location', "BreakAway Field %s" % game.field)
            event['uid'] = '%s/%s@breakawaysports.com' % (now_string, shortuuid.uuid())
            event.add('priority', 5)
            cal.add_component(event)

        ics_file = open('ics/Master Schedule.ics', 'wb')
        ics_file.write(cal.to_ical())
        ics_file.close()