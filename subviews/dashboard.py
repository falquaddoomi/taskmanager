from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from taskmanager.models import *

from datetime import datetime

# either renders a section or embeds it in the main page and renders it, depending on xhr
def fleshify(request, patientid, section, section_url, field_vars):
    # we need these most of the time, so we'll just throw them in
    field_vars['selected_patientid'] = patientid
    field_vars['current_page'] = request.path
    
    if request.is_ajax():
        # just render this shard
        return render_to_response(section_url, field_vars)
    else:
        # add in the list of users so we can draw the user chooser
        field_vars['patients'] = Patient.objects.all()
        field_vars['section'] = section
        field_vars['section_url'] = section_url
        # and render the full page
        return render_to_response('dashboard/main.html', field_vars)

def profile(request, patientid):
    field_vars = {
        'patient': Patient.objects.get(pk=patientid)
        }
    
    return fleshify(request, patientid, "profile", "dashboard/sections/profile.html", field_vars)

def processes(request, patientid):
    field_vars = {}
    return fleshify(request, patientid, "processes", "dashboard/sections/processes.html", field_vars)

def tasks(request, patientid):
    field_vars = {
        'tasktemplates': TaskTemplate.objects.all(),
        'pending_tasks': ScheduledTask.objects.filter(patient__id=patientid,completed=False).order_by('schedule_date'),
        'current_sessions': Session.objects.get_current_sessions().filter(patient__id=patientid).order_by('add_date'),
        'completed_sessions': Session.objects.get_completed_sessions().filter(patient__id=patientid).order_by('add_date'),
        }
    
    return fleshify(request, patientid, "tasks", "dashboard/sections/tasks.html", field_vars)

def dispatch(request, patientid, section):
    if section == "profile":
        return profile(request, patientid)
    elif section == "processes":
        return processes(request, patientid)
    elif section == "tasks":
        return tasks(request, patientid)

    return HttpResponseNotFound()

def default(request):
    # add in the list of users so we can draw the user chooser
    field_vars = {
        'patients': Patient.objects.all()
        }
    
    # and render the full page
    return render_to_response('dashboard/main.html', field_vars)

# =================================================================
# ==== Forms for adding ScheduledTasks, Processes
# =================================================================

from django import forms

class ScheduledTaskForm(forms.Form):
    task = forms.ModelChoiceField(queryset=TaskTemplate.objects.all(), empty_label=None)
    scheduled_date = forms.DateField()
    scheduled_time = forms.TimeField()
    
def add_scheduled_task(request):
    if request.method == 'POST': # If the form has been submitted...
        try:
            template = TaskTemplate.objects.get(pk=int(request['tasktemplate']))
            
            nt = ScheduledTask(
                patient = Patient.objects.get(pk=int(request.POST['patient'])),
                task = template.task,
                schedule_date = datetime.strptime(request.POST['scheduled_date'] + " " + request.POST['scheduled_time'], "%m/%d/%Y %I:%M%p"),
                arguments = template.arguments
            )
            nt.save()

            # return HttpResponseRedirect(reverse('taskmanager.views.scheduler'))
            return HttpResponseRedirect(request.POST['return_page'])
        except:
            response = HttpResponse()
            response.write("<b>error:</b> task could not be scheduled (" + sys.exc_info()[0] + ")")
            return response
    
