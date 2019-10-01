from notifiers import Notifier

class HttpCallbackNotifier(Notifier):

    def notify(self, run, state, message): #TODO
        "Send a message to the configured URL via http-form POST"
        pass
