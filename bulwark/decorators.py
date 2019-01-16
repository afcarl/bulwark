# -*- coding: utf-8 -*-
import functools
import sys
from inspect import getfullargspec, getmembers, isfunction

import bulwark.checks as ck
from bulwark.generic import snake_to_camel


class BaseDecorator(object):
    """Turns a given function into a decorator.

    Args:
        enabled (bool): Determines if the decorator (check function) will be run.
        *args: Arguments to pass through to the check function.
        **kwargs: Keyword arguments to pass through to the check function.

    """

    def __init__(self, *args, **kwargs):  # how to take args in decorator..?
        self.enabled = True  # setter to enforce bool would be a lot safer, but challenge w/ decorator
        # self.warn = False ? No - put at func level for all funcs and pass through
        self.params = getfullargspec(self.check_func).args[1:]

        self.__dict__.update(dict(zip(self.params, args)))
        self.__dict__.update(**kwargs)

    def __call__(self, f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            df = f(*args, **kwargs)
            if self.enabled:
                kwargs = {k: v for k, v in self.__dict__.items() if k not in ["check_func", "enabled", "params"]}
                self.check_func(df, **kwargs)
            return df
        return decorated


def decorator_factory(decorator_name, func):
    """Takes in a function and outputs a class that can be used as a decorator."""
    class decorator_name(BaseDecorator):
        # todo add the fact that it's a decorated version of func
        # todo remove df from the functions arg list, since it's automatically fed to the decorated version
        # todo overwrite Returns

        # docstring = func.__doc__
        # begin_df = docstring.find("df (pd.DataFrame):")
        # # identifies white spaces before begin_df, but after the new line
        # new_sec_whitespace = docstring[begin_df - docstring[begin_df - 1::-1].find("\n"): begin_df]
        # rgx = f"(\n { {len(new_sec_whitespace)} })[^\s]"
        # end_df = begin_df + re.search(rgx, docstring[begin_df:]).start() + 1
        # __doc__ = docstring[:begin_df] + docstring[end_df + len(new_sec_whitespace):]

        __doc__ = func.__doc__
        check_func = staticmethod(func)

    return decorator_name


# Automatically creates decorators for each function in bulwark.checks
this_module = sys.modules[__name__]
check_functions = [func[1] for func in getmembers(ck, isfunction) if func[1].__module__ == 'bulwark.checks']

for func in check_functions:
    decorator_name = snake_to_camel(func.__name__)
    setattr(this_module, decorator_name, decorator_factory(decorator_name, func))


""" ToDo: fit this into BaseDecorator paradigm

CustomCheck might need its own full class instead of using BaseDecorator
This code is below the auto-generation of decorators, so this overwrites the auto-generated CustomCheck.

"""


def _custom_check(check_func, *args, **kwargs):
    def decorate(operation_func):
        @functools.wraps(operation_func)
        def wrapper(*operation_args, **operation_kwargs):
            df = operation_func(*operation_args, **operation_kwargs)
            ck.custom_check(check_func, df, *args, **kwargs)
            return df
        return wrapper
    return decorate


def CustomCheck(check_func, *args, **kwargs):
    """Assert that `func(df, *args, **kwargs)` is true."""
    return _custom_check(check_func, *args, **kwargs)
