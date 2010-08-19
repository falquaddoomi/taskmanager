import rapidsms
import machine

from datetime import datetime
import parsedatetime.parsedatetime as pdt
import parsedatetime.parsedatetime_consts as pdc

class AppointmentFollowupMachine(machine.BaseMachine):
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
        msg.subject = "Appointment Reminder"
        msg.text = """Hello, %s. Just letting you know that you scheduled an appointment for %s.
You don't have to respond if you're ok with that date.
If you'd like to reschedule, text me back a new date. If you'd like to cancel, text me back 'cancel' or 'no'.
        """ % (self.patient.first_name, self.args.appt_date)
        msg.send()

        self.state = 'awaiting_response'

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
        text = message.text.strip().lower()
        
        # parse the message and determine the transition
        if text == "cancel" or text == "no":
            # they want to cancel their appointment, so let them know and don't do anything else
            message.respond("Your appointment has been cancelled. You will be notified if you need to schedule a new appointment. Thank you!")
            return None

        # attempt to parse a date out of the message
        p = pdt.Calendar()
        result = p.parse(text)

        if (result[1] == 0):
            # we send them a "sorry" message...alternatively, we could throw an Unparseable
            # and let some other state machine take a crack at it
            message.respond("Sorry, I couldn't understand your input; please try again.")
            return 'awaiting_response'
        else:
            # the date they chose is in result[0]
            reminder_date = p.parse("3 days ago", result[0])
	    reminder_date_datetime = datetime.fromtimestamp(time.mktime(reminder_date[0]))
            # schedule a task to remind them before that date and exit this machine for now
            self.schedule_task("AppointmentReminder", reminder_date_datetime, arguments={
                    'appt_date': datetime(result[0])
                }.update(self.args))
            message.respond("Thank you; your appointment is scheduled for %s.", datetime(result[0]))
            return None
        
