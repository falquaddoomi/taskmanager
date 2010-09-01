import rapidsms
import machine, appt_machine

from django.template import Context, Template

from datetime import datetime, timedelta
import parsedatetime.parsedatetime as pdt
import parsedatetime.parsedatetime_consts as pdc

from taskmanager.models import *

# to access the reschedule() method
from appt_request import AppointmentRequestMachine

class AppointmentReminderMachine(appt_machine.BaseAppointmentMachine):
    def __init__(self, session, router, patient, args):
        super(AppointmentReminderMachine, self).__init__(session, router, patient, args)

        # init our dispatch table 
        self.state_dispatch = {
                'awaiting_response': self.AwaitingResponseState
            }
        self.state = 'idle'

    def start(self):
        # we assume that we have a reference to the patient
        # send them a nice greeting message
        conn = rapidsms.connection.Connection(self.router.get_backend('email'), self.patient.address)
        message = rapidsms.message.EmailMessage(connection=conn)
        message.subject = "Appointment Reminder"
        if 'nocancel' in self.args:
            t = Template("""{% load parse_date %}Hello, {{ patient.first_name }}. You have an appointment {% if args.daybefore %}tomorrow{% else %}today{% endif %} at {{ args.appt_date|parse_date|time }}.
{% if args.requires_fasting %}Please do not eat or drink anything (except water) for at least 9 hours before your test.{% endif %}""")
            message.text =  t.render(Context({'patient': self.patient, 'args': self.args}))
            message.send()
            self.log_message(message.text, outgoing=True)
            return None
        else:
            t = Template("""{% load parse_date %}Hello, {{ patient.first_name }}. Just letting you know that you scheduled an appointment for {{ args.appt_date|parse_date|date }}, {{ args.appt_date|parse_date|time }}.
You don't have to respond if you're ok with that date.
If you'd like to reschedule, text me back a new date. If you'd like to cancel, text me back 'cancel' or 'no'.""")
            message.text =  t.render(Context({'patient': self.patient, 'args': self.args}))
            message.send()
            self.log_message(message.text, outgoing=True)
            # set a timeout so that the session eventually ends
            self.set_timeout(datetime.now() + timedelta(hours=4))
            # and wait for a response
            self.state = 'awaiting_response'
            
            return True # return True because we want this to continue

    def handle(self, message):
        self.log_message(message.text, outgoing=False)
        
        try:
            # execute our current state and get our new state from it
            self.state = self.state_dispatch[self.state](message)
        except machine.UnparseableException:
            # we can't handle it if we can't even parse it
            return False

        if self.state is None:
            # we're in a terminal state; allow the task manager to destroy us
            return None

        # we handled it and moved on to a new state, indicate as much
        return True

    # ==================================================
    # === definitions for each of our states are below
    # ==================================================

    def AwaitingResponseState(self, message):
        text = message.text.strip().lower()
        
        # parse the message and determine the transition
        if text == "cancel" or text == "no":
            # they want to cancel their appointment, so let them know and don't do anything else
            message.text = "Your appointment has been cancelled. You will be notified if you need to schedule a new appointment. Thank you!"
            message.respond(message.text)
            self.log_message(message.text, outgoing=True)
            return None

        # attempt to parse a date out of the message
        p = pdt.Calendar()
        result = p.parse(text)

        if (result[1] == 0):
            # we send them a "sorry" message...alternatively, we could throw an Unparseable
            # and let some other state machine take a crack at it
            message.text = "Sorry, I couldn't understand your input; please try again."
            message.respond(message.text)
            self.log_message(message.text, outgoing=True)
            # reset the timeout to give them a chance to respond
            self.set_timeout(datetime.now() + timedelta(hours=4))
            return 'awaiting_response'
        else:
            # the date they chose is in result[0]
            self.reschedule(message, result[0])
            return None
        
