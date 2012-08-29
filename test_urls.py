from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^likes/', include('likes.urls')),
)
