from datetime import date
from django.db import models
from smart_selects.db_fields import ChainedForeignKey


class Organization(models.Model):
    name = models.CharField(max_length=25)
    is_enabled = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class League(models.Model):
    name = models.CharField(max_length=100)
    org = models.ForeignKey(Organization)
    key = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s" % self.name


class Field(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=300, blank=True, null=True)
    is_open = models.BooleanField(default=True)
    maps_link = models.URLField(verbose_name="Maps", blank=True, null=True)

    def __unicode__(self):
        return self.name


class Staff(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.name


class Team(models.Model):
    number = models.IntegerField()
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100, blank=True, null=True)
    club = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    league = models.ForeignKey(League)
    manager = models.ForeignKey(Staff, blank=True, null=True, related_name='manager')
    coach = models.ForeignKey(Staff, blank=True, null=True, related_name='coach')

    class Meta:
        ordering = ['number']

    def __unicode__(self):
        return u"[%s] %s" % (self.number, self.name)


class Game(models.Model):
    league = models.ForeignKey(League)
    date = models.DateField()
    time = models.TimeField()
    field = models.ForeignKey(Field)
    referee = models.ForeignKey(Staff, null=True, blank=True)

    home_team = ChainedForeignKey(Team,
                                  chained_field='league',
                                  chained_model_field='league',
                                  related_name='home_team')
    away_team = ChainedForeignKey(Team,
                                  chained_field='league',
                                  chained_model_field='league',
                                  related_name='away_team')

    @property
    def is_today(self):
        if self.time.date() == date.today():
            return True
        else:
            return False

    @property
    def color_conflict(self):
        if self.home_team.color.upper() == self.away_team.color.upper():
            return True
        else:
            return False

    class Meta:
        ordering = ['time']

    def __unicode__(self):
        return u"%s vs. %s" % (self.home_team.name, self.away_team.name)
