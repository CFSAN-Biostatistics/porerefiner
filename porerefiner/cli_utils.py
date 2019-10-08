"Custom argument handler types for Click"

import click

#these two functions are hooks in case we decide to store only relative paths.
#paths going into the database will be relativized; paths going out will be
#absolutized.
#Whatever they do, they need to invert each other
def relativize_path(path):
    return path

def absolutize_path(path):
    return path

class RunID:
    "can be either a string name or a numeric id"

    RUN_NAME = 'RUN_NAME'
    RUN_ID = 'RUN_ID'

    def __init__(self, the_value):
        if isinstance(the_value, str):
            self.val_type = RUN_NAME
        elif isinstance(the_value, int):
            self.val_type = RUN_ID
        else:
            raise ValueError("value must be str or int")



class ValidRunID(click.ParamType):

    def convert(self, value, param, ctx):
        try:
            return RunID(int(value))
        except ValueError:
            return RunID(value)

VALID_RUN_ID = ValidRunID()
