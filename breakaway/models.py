from django.db import models


class League(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Team(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    league = models.ForeignKey('League', related_name='teams')

    def __unicode__(self):
        return "[%s] %s [%s]" % (self.id, self.name, self.color)


class Game(models.Model):
    home_team = models.ForeignKey('Team', related_name="home_team")
    away_team = models.ForeignKey('Team', related_name="away_team")
    time = models.DateTimeField()
    field = models.IntegerField()

    def __unicode__(self):
        return "%s vs. %s" % (self.home_team, self.away_team)