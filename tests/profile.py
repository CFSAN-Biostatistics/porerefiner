

import timeit
import click


def start_pr():
    pass

def stop_pr():
    pass


click.argument('n', default=1000)
click.command()
def performanceOnNFiles(self, n=3000):
    
    def fs_spray():
        pass

    basetime = timeit.timeit("fs_spray()", number=n)
    start_pr()
    realtime = timeit.timeit("fs_spray()", number=n)
    stop_pr()
    click.echo(realtime - basetime)
