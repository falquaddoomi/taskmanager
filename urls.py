#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import taskmanager.views as views
import taskmanager.subviews.login as login
import taskmanager.subviews.dashboard as dashboard
import taskmanager.subviews.details as details

urlpatterns = patterns('',
    (r'^taskmanager/$', dashboard.default),
    (r'^taskmanager/login$', login.prompt_login),
    (r'^taskmanager/logout$', login.perform_logout),
    (r'^taskmanager/patients/(?P<patientid>\d+)/(?P<section>[a-zA-Z]+)/?$', dashboard.dispatch),

    (r'^taskmanager/tasks/add/?$', dashboard.add_scheduled_task),
    (r'^taskmanager/processes/add/?$', dashboard.add_scheduled_process),
    (r'^taskmanager/patients/add/?$', dashboard.add_patient),

    (r'^taskmanager/tasktemplates/(?P<tasktemplateid>\d+)/fields/?$', dashboard.get_tasktemplate_fields),

    (r'^taskmanager/processes/(?P<processid>\d+)/details/?$', details.process_details),
    (r'^taskmanager/tasks/(?P<taskid>\d+)/details/?$', details.scheduledtask_details),
    (r'^taskmanager/sessions/(?P<sessionid>\d+)/details/?$', details.session_details),
    (r'^taskmanager/patients/(?P<patientid>\d+)/details/?$', details.patient_details),

    (r'^taskmanager/processes/(?P<processid>\d+)/command/?$', details.process_command),
    (r'^taskmanager/tasks/(?P<taskid>\d+)/command/?$', details.scheduledtask_command),
    (r'^taskmanager/sessions/(?P<sessionid>\d+)/command/?$', details.session_command),
                       
    (r'^taskmanager/scheduler/?$', views.scheduler),
    (r'^taskmanager/scheduler/add/?$', views.add_scheduled_task),
    (r'^taskmanager/scheduler/check_service$', views.check_scheduler),

    (r'^proxy/(?P<url>.+)$', views.proxy)
)
