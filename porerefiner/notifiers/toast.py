from porerefiner.notifiers import Notifier

class ToastNotifier(Notifier): #TODO
    "Notifier that throws up an OS 'toast' on Windows, Ubuntu, and CentOS"

    def notify(self, run, state, message):
        pass
