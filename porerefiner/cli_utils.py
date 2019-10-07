"Custom argument handler types for Click"

import click


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
