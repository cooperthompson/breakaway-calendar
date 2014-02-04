from django.db import models


class Season(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class League(models.Model):
    name = models.CharField(max_length=100)
    season = models.ForeignKey('Season', related_name='leagues')

    def __unicode__(self):
        return "%s" % self.name


class Team(models.Model):
    number = models.IntegerField()
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    league = models.ForeignKey('League', related_name='teams')

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return "[%s] %s (%s)" % (self.number, self.name, self.color)


class Game(models.Model):
    home_team = models.ForeignKey('Team', related_name="home_team")
    away_team = models.ForeignKey('Team', related_name="away_team")
    time = models.DateTimeField()
    field = models.IntegerField(default=1)

    def __unicode__(self):
        return "%s vs. %s @%s" % (self.home_team, self.away_team, self.time)