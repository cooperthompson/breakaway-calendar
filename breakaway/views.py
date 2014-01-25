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
