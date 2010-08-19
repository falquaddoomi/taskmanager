import rapidsms
import machine

from datetime import datetime
import time
import parsedatetime.parsedatetime as pdt
import parsedatetime.parsedatetime_consts as pdc

class AppointmentRequestMachine(machine.BaseMachine):
    def __init__(self, session, router, patient, args):
        super(AppointmentRequestMachine, self).__init__(session, router, patient, args)

        # init our dispatch table 
        self.state_dispatch = {
                'awaiting_response': self.AwaitingResponseState
            }
        self.state = 'idle'

    def start(self):
        # we assume that we have a reference to the patient
        # send them a nice greeting message
        conn = rapidsms.connection.Connection(self.router.get_backend('email'), self.patient.address)
        msg = rapidsms.message.EmailMessage(connection=conn)
        msg.subject = "Appointment Schedule Request"
        msg.text = """Hello, %s; you're due for a %s soon.
If you'd like to schedule one now, text me back a date.
Text back 'no' or ignore this message if you don't want to schedule anything now.
        """ % (self.patient.first_name, self.args['appt_type'])
        msg.send()

        self.state = 'awaiting_response'

        return True # we handled it, thus return True

    def handle(self, message):
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
        # parse the message and determine the transition
        if message.text.strip().lower() == "no":
            # we shouldn't bother them anymore
            return None

        # attempt to parse a date out of the message
        p = pdt.Calendar()
        result = p.parse(message.text)

        if (result[1] == 0):
            # we send them a "sorry" message...alternatively, we could throw an Unparseable
            # and let some other state machine take a crack at it
            message.respond("Sorry, I couldn't understand your input; please try again.")
            return 'awaiting_response'
        else:
            # the date they chose is in result[0]
            appt_date_datetime = datetime.fromtimestamp(time.mktime(result[0]))
            
            reminder_date = p.parse("3 days ago", result[0])
            reminder_date_datetime = datetime.fromtimestamp(time.mktime(reminder_date[0]))
            
            morning_reminder_date = p.parse("8am", result[0])
            morning_reminder_datetime = datetime.fromtimestamp(time.mktime(morning_reminder_date[0]))

            # schedule a task to remind them before that date
            self.schedule_task("AppointmentReminderMachine", reminder_date_datetime, arguments={
                    'appt_date': time.asctime(result[0])
                }.update(self.args))
            # schedule a task to remind them the morning of, too
            self.schedule_task("AppointmentReminderMachine", morning_reminder_datetime, arguments={
                    'appt_date': time.asctime(result[0])
                }.update(self.args))
            message.respond("Thank you; your %s is scheduled for %s. You'll be reminded on %s and the morning of the appointment." % (self.args['appt_type'], appt_date_datetime, reminder_date_datetime))
            return None
        
