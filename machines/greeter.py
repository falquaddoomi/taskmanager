import rapidsms
import machine

class GreeterMachine(machine.BaseMachine):
    def __init__(self, session, router, patient, args):
        super(GreeterMachine, self).__init__(session, router, patient, args)
        self.state = 'idle'

    def start(self):
        # we assume that we have a reference to the patient
        # send them a nice greeting message
        conn = rapidsms.connection.Connection(self.router.get_backend('email'), self.patient.address)
        msg = rapidsms.message.EmailMessage(connection=conn)
        msg.subject = "Greeter Automated Message"
        msg.text = "Hello, %s %s!" % (self.patient.first_name, self.patient.last_name)
        msg.send()
        return None # returning None because this machine is done

    def handle(self, message):
        # we're going to try to figure out what they're talking about
        message.respond("Hey, %s! Glad to hear from you!" % self.patient.first_name)
        return None # no one should ever get here because the handler should be removed
