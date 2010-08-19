import rapidsms
import sys, json, re

from taskmanager.models import *
from datetime import datetime

class App(rapidsms.app.App):
    def start(self):
        # maps patients to their state machines -- indexed for now
        self.dispatch = {}
        # holds references to dynamically loaded machine classes
        self.machines = {}

        # also load up all the different kinds of state machines
        tasks = Task.objects.all()

        for task in tasks:
            curModule = __import__(task.module, globals(), locals(), [task.className])
            self.machines[task.id] = curModule.__dict__[task.className]

        # clear the Session table, since obviously nothing is actually running
        Session.objects.filter(completed=False).delete()
        
    def handle(self, message):
        self.debug("got message %s", message.text)

        # we found a patient; let them handle the message
        if message.peer in self.dispatch:
            result = self.dispatch[message.peer].handle(message)

            # look up our Session to either update or remove it depending on the result
            session = self.dispatch[message.peer].session
            
            # if the result is None, consider it handled and deattach this machine
            if result == None:
                # mark session as completed
                session.completed_date = datetime.now()
                session.completed = True
                session.save()
                # also delete the machine instance itself from our dispatch
                del self.dispatch[message.peer]
                return True
            else:
                # set the Session's state to reflect the machine's internal state
                try:
                    session.state = self.dispatch[message.peer].get_state()
                except:
                    session.state = sys.exc_info()[0] # we can't set the state because we don't know it :|
                session.save()
                return result

        # it's not for a subscribed patient, so we can't handle it
        return False

    def ajax_GET_status(self, getargs, postargs=None):
        return self.dispatch

    def ajax_POST_exec(self, getargs, postargs=None):
        task = Task.objects.get(pk=postargs['task'])
        patient = Patient.objects.get(pk=postargs['patient'])
        args = json.loads(postargs['arguments'])

        if 'process' in postargs:
            process = Process.objects.get(pk=postargs['process'])
        else:
            process = None

        # extract the patient, pass the args to the state machine we create
        # try:
        if not patient in self.dispatch:
            # create a Session in the db to manage this machine instance
            session = Session(patient=patient, task=task, process=process, state='unknown')
            session.save()
            
            # attempt to create a state machine for the given task
            self.dispatch[patient.address] = self.machines[task.id](session, self.router, patient, args)
            # run the start event on the machine (which may put us in a terminal or nonterminal state)
            result = self.dispatch[patient.address].start()

            # try:
            session.state = self.dispatch[patient.address].get_state()
            #except:
            #    rt.state = sys.exc_info()[0] # we can't set the state because we don't know it :|
            
            if result == None:
                # mark session as completed
                session.completed_date = datetime.now()
                session.completed = True
                # remove from dispatch table
                del self.dispatch[patient.address]

            # save the session regardless of what happens
            session.save()
        else:
            # re-run it for this patient, i guess
            # self.dispatch[patient.address].start()
            return {'status': 'ERROR', 'msg': '%s is already in the system' % patient}
        # except:
        #    print "Ran into a nasty exception: %s" % sys.exc_info()[0]
        #    return {'status': 'ERROR', 'msg': re.escape(sys.exc_info()[0]))}

        # since we haven't returned yet, it must mean we're good
        return {'status': 'OK'}
