import codecs
import pdb
from datetime import datetime, timedelta, date
import re
import os
import glob
from django.core.management.base import BaseCommand
from breakaway.models import *
from django.conf import settings


class Command(BaseCommand):
    args = '<txt_file txt_file ...>'
    help = 'Load team data into the database'

    def __init__(self):
        super(Command, self).__init__()
        self.season = ""
        self.league = ""

        # clear out existing data
        Game.objects.all().delete()
        Team.objects.all().delete()
        League.objects.all().delete()
        Season.objects.all().delete()

    def handle(self, *args, **options):

        plain_txt_files = self.get_txt_files(0)
        layout_txt_files = self.get_txt_files(1)

        # Load game data from files
        for txt_filename in layout_txt_files:
            self.stdout.write("Loading teams from %s" % txt_filename)
            self.process_team_file(txt_filename)

        # Load game data from files
        for txt_filename in plain_txt_files:
            self.stdout.write("Loading games from %s" % txt_filename)
            self.process_game_file(txt_filename)

    @staticmethod
    def get_txt_files(layout):
        txt_files = []

        import_dir = os.path.join(settings.BASE_DIR, "import")
        os.chdir(import_dir)

        if layout:
            file_list = glob.glob('*-layout.txt')
        else:
            file_list = glob.glob('*-plain.txt')

        for filename in file_list:
            txt_files.append(filename)

        return txt_files

    def process_team_file(self, text_filename):
        self.league = self.get_league(text_filename)
        text_file = open(text_filename, "r")
        mode = "start"

        for line in text_file:
            if "TEAM (COLOR)" in line.strip():
                mode = "team"
            if "QUICK NOTES" in line.strip():
                mode = "team-complete"
            if line.strip() == "WEEK 1":
                mode = "sched"
            if "IMPORTANT EVERYONE READ" in line.strip():
                mode = "sched-complete"

            if mode == "team" and re.match("\d+.*", line.strip()):
                self.save_team(line)

    def save_team(self, line):
        """
        @param line: A single lien from the PDF to be parsed for team data
        """
        #matches = re.findall("\s*(\d+)\.?\s+(.*)\s+(\d+)\.\s+(.*)", line)
        matches = re.findall("(\d+)\.\s+(.*?)\((.*?)\)", line)
        for match in matches:
            self.stdout.write("Processing match: %s" % (match,))
            team_id = match[0]
            team_name = match[1]
            team_color = match[2]
            team = Team(number=int(team_id),
                        name=team_name,
                        color=team_color,
                        league=self.league)
            team.save()

    def get_league(self, text_filename):
        match = re.match(".*\.(.*).txt", text_filename)
        if match:
            key = match.group(1).replace("-layout", "").replace("-plain", "")
        else:
            self.stderr.write("Couldn't figure out what league this is for")

        try:
            league = League.objects.get(key=key)
        except League.DoesNotExist:
            self.stderr.write("Couldn't find league %s.  Creating on-the-fly." % key)

            # default the name to be the key.
            # the name can be updated in the admin GUI to something user-readable.
            # The key should never be changed.
            league = League(name=key,
                            key=key)
            league.save()
        return league

    def process_game_file(self, text_filename):
        self.league = self.get_league(text_filename)

        #text_file = open(text_filename, "r")
        text_file = codecs.open(text_filename, encoding='utf-8', mode='r')

        mode = "start"
        game_date = "0"

        #if self.league.key != "coedsocialw31314":
        #    return

        while True:
            line = text_file.readline()
            if not line:
                break  # EOF

            if "TEAM (COLOR)" in line.strip():
                mode = "team"
            if "QUICK NOTES" in line.strip():
                mode = "team-complete"
            if "WEEK 1" in line.strip():
                mode = "sched"
            if "IMPORTANT EVERYONE READ" in line.strip():
                mode = "sched-complete"

            if mode == "sched":
                #print repr(line)
                pass

            # regex check for the date row (i.e. Mo.Feb 3)
            match = re.match("(\w+)\.?(\w+)\.?\s+(\d+)", line)
            if mode == "sched" and match:
                game_date = line

            # regex check for the game row (i.e. 19-20 7:002)
            match = re.match("(\d+)-(\d+) (\d+:\d{2})(\d?)", line)
            if mode == "sched" and match:
                home_team_number = int(match.group(1))
                away_team_number = int(match.group(2))
                try:
                    home_team = Team.objects.filter(league=self.league).get(number=home_team_number)
                except Team.DoesNotExist:
                    self.stdout.write("Couldn't find team %s in league %s" % (home_team_number, self.league))
                    return

                try:
                    away_team = Team.objects.filter(league=self.league).get(number=away_team_number)
                except Team.DoesNotExist:
                    self.stdout.write("Couldn't find team %s in league %s" % (away_team_number, self.league))
                    return

                game_time = match.group(3)
                field = match.group(4)
                if not field:
                    field = 1

                if game_date == "0":
                    self.stdout.write("Couldn't find the correct date info.")
                    self.stdout.write("   %s" % line)
                    return

                game_time = self.parse_pdf_datetime(game_date, game_time)
                if not game_time:
                    self.stdout.write("Unable to determine game date/time: %s/%s" % (game_date, game_time))
                    return

                game = Game(home_team=home_team,
                            away_team=away_team,
                            time=game_time,
                            field=field)
                self.stdout.write("Loaded game %s" % repr(game))
                try:
                    game.save()
                except Exception as e:
                    pdb.set_trace()

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

                home_team_number = int(match_mtch.group(1))
                away_team_number = int(match_mtch.group(2))

                try:
                    home_team = Team.objects.filter(league=self.league).get(number=home_team_number)
                except Team.DoesNotExist:
                    self.stdout.write("Couldn't find team %s in league %s" % (home_team_number, self.league))
                    return

                try:
                    away_team = Team.objects.filter(league=self.league).get(number=away_team_number)
                except Team.DoesNotExist:
                    self.stdout.write("Couldn't find team %s in league %s" % (away_team_number, self.league))
                    return

                try:
                    game_time = match_time.group(1)
                except AttributeError as e:
                    self.stdout.write("Unable to parse game info:")
                    self.stdout.write("   line1: %s" % line)
                    self.stdout.write("   line2: %s" % line2)
                    return

                field = match_time.group(2)
                if not field:
                    field = 1

                game_time = self.parse_pdf_datetime(game_date, game_time)
                if not game_time:
                    self.stdout.write("Unable to determine game date/time: %s/%s" % (game_date, game_time))
                    return

                game = Game(home_team=home_team,
                            away_team=away_team,
                            time=game_time,
                            field=field)
                self.stdout.write("Loaded game %s" % repr(game))
                game.save()

        return

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

            if game_hr != 12:
                game_hr += 12  # covert to 24 hour time.  Always assume games are in the evening..

            game_dt = int(game_dt)
            try:
                game_datetime = datetime(game_year, game_month, game_dt, game_hr, game_mn)
            except ValueError as e:
                pdb.set_trace()

            #print game_datetime.strftime("%A, %B %d,  %Y  %I:%M %p")
        else:
            self.stdout.write(date_string)
            game_datetime = None
        return game_datetime