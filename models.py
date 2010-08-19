#!/usr/bin/env python

import django
from django.db import models
from django.contrib.auth.models import User

from datetime import datetime

# =================================================================
# ==== Users
# =================================================================

class Patient(models.Model):
    address = models.CharField(max_length=200)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)

    def __unicode__(self):
        return "%s, %s (%s)" % (self.last_name, self.first_name, self.address)

class Clinician(models.Model):
    # links the Clinician object to a User object for authentication purposes
    user = models.ForeignKey(User, unique=True)

# =================================================================
# ==== Task Descriptions
# =================================================================

class Task(models.Model):
    name = models.CharField(max_length=100)
    module = models.CharField(max_length=100)
    className = models.CharField(max_length=100)
    schedulable = models.BooleanField(blank=True,default=False)

    def __unicode__(self):
        return "%s (%s.%s)" % (self.name, self.module, self.className)

class TaskTemplate(models.Model):
    name = models.CharField(max_length=100)
    task = models.ForeignKey(Task)
    arguments = models.TextField(blank=True)

    def __unicode__(self):
        return "%s" % (self.name)

# =================================================================
# ==== Processes (Scheduled Task + Session Group)
# =================================================================

class ProcessManager(models.Manager):
    def get_pending_processes(self):
        # a pending process has only incomplete scheduled tasks
        qset = super(SessionManager, self).get_query_set()
        return qset.filter(completed_date__isnull=True, completed=False)
    
    def get_current_processes(self):
        # a current process has at least one incomplete session
        qset = super(SessionManager, self).get_query_set()
        return qset.filter(completed_date__isnull=True, completed=False)

    def get_completed_processes(self):
        # a completed process has only complete scheduled tasks and sessions
        qset = super(SessionManager, self).get_query_set()
        return qset.filter(completed_date__isnull=False, completed=True)
    
class Process(models.Model):
    name = models.CharField(max_length=100)
    add_date = models.DateTimeField(auto_now_add=True)

    objects = ProcessManager()

# =================================================================
# ==== Sessions and Logging/Data Collection
# =================================================================

class SessionManager(models.Manager):
    def get_current_sessions(self):
        qset = super(SessionManager, self).get_query_set()
        return qset.filter(completed_date__isnull=True, completed=False)

    def get_completed_sessions(self):
        qset = super(SessionManager, self).get_query_set()
        return qset.filter(completed_date__isnull=False, completed=True)

class Session(models.Model):
    patient = models.ForeignKey(Patient)
    task = models.ForeignKey(Task)
    process = models.ForeignKey(Process,null=True)
    add_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(blank=True,default=False)
    completed_date = models.DateTimeField(blank=True,null=True)
    state = models.CharField(max_length=100)

    objects = SessionManager()
    
    def __unicode__(self):
        return "Session for %s on %s" % (self.patient.address, self.task.name)

class SessionMessage(models.Model):
    session = models.ForeignKey(Session)
    message = models.TextField()
    outgoing = models.BooleanField()
    add_date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        if self.outgoing:
            return "Sent to %s: %s" % (self.session.patient.address, self.message)
        else:
            return "Received from %s: %s" % (self.session.patient.address, self.message)
    
class TaskPatientDatapoint(models.Model):
    patient = models.ForeignKey(Patient)
    task = models.ForeignKey(Task)
    add_date = models.DateTimeField(auto_now_add=True)
    data = models.TextField()

    def __unicode__(self):
        return "Datapoint for %s on %s" % (self.patient.address, self.task.name)

# =================================================================
# ==== Scheduled tasks
# =================================================================

class ScheduledTaskManager(models.Manager):
    def get_pending_tasks(self):
        qset = super(ScheduledTaskManager, self).get_query_set()
        return qset.filter(schedule_date__gt=datetime.now(), completed=False)

    def get_due_tasks(self):
        qset = super(ScheduledTaskManager, self).get_query_set()
        return qset.filter(schedule_date__lte=datetime.now(), completed=False)

    def get_past_tasks(self):
        qset = super(ScheduledTaskManager, self).get_query_set()
        return qset.filter(schedule_date__lte=datetime.now(), completed=True)

class ScheduledTask(models.Model):
    patient = models.ForeignKey(Patient)
    task = models.ForeignKey(Task)
    process = models.ForeignKey(Process,null=True)
    add_date = models.DateTimeField(auto_now_add=True)
    arguments = models.TextField(blank=True)
    schedule_date = models.DateTimeField()
    completed = models.BooleanField(blank=True,default=False)
    completed_date = models.DateTimeField(blank=True,null=True)
    result = models.TextField(blank=True)

    objects = ScheduledTaskManager()

    def is_pending(self):
        return (self.schedule_date > datetime.now()) and (not self.completed)

    def is_due(self):
        return (self.schedule_date <= datetime.now()) and (not self.completed)

    def is_past(self):
        return (self.schedule_date <= datetime.now()) and (self.completed)

    def get_status(self):
        if self.is_pending(): return "pending"
        elif self.is_due(): return "due"
        elif self.is_past(): return "past"
        else: return "unknown"

    def __unicode__(self):
        return "Scheduled Task for %s on %s" % (self.patient.address, self.task.name)
