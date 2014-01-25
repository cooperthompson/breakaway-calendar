from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'breakaway.views.home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
)
