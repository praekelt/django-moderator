from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext


def home(request):
    user = User.objects.get(id=1)
    return render_to_response('home.html', {'user': user}, context_instance=RequestContext(request))
