from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', 'breakaway.views.home', name='home'),
                       url(r'^team/(?P<team_id>.+)/$', 'breakaway.views.team', name='team'),
                       url(r'^league/(?P<league_id>.+)/$', 'breakaway.views.league', name='league'),
                       url(r'^ics/Master.ics', 'breakaway.views.master_ics', name='master_ics'),
                       url(r'^ics/(?P<team_name>.+).ics', 'breakaway.views.ics', name='ics'),
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^chaining/', include('smart_selects.urls')),
                       (r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
                       (r'^admin/',  include(admin.site.urls)),  # admin site
)


