from django.conf.urls import *
from omero_graph import views

urlpatterns = patterns('django.views.generic.simple',

    url(r'^$', views.index, name='graphs'), 
 )