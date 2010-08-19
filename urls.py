#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import taskmanager.views as views
import taskmanager.subviews.dashboard as dashboard

urlpatterns = patterns('',
    (r'^taskmanager/$', dashboard.default),
    (r'^taskmanager/patients/(?P<patientid>\d+)/(?P<section>[a-zA-Z]+)/?$', dashboard.dispatch),
    (r'^taskmanager/scheduler/add/?$', dashboard.add_scheduled_task),
                       
    (r'^taskmanager/scheduler/?$', views.scheduler),
    (r'^taskmanager/scheduler/check_service$', views.check_scheduler)
)
