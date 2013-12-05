"""

Since our development environment is controlled completely by passing
environment variables from one process to its children, in generaly allow all
variables to flow freely. There are, however, a few circumstances in which we
need to inhibit this flow.

Maya and Nuke, for example, add to the :envvar:`python:PYTHONHOME`, and our
launchers add to :envvar:`PYTHONSITES` (for PyQt, etc.). These changes must
not propigate to other processes.

These tools allow us to manage those variables which should not propigate.
Upon Python startup, these tools will reset any variables which have been flagged.


Actual Variables
----------------
.. envvar:: PYTHONENVIRONDIFF

    A set of variables to update (or delete) from Python's :data:`os.environ`
    at startup. This is used to force variables that are nessesary for startup
    to not propigate into the next executable.
    
    .. warning:: Do not use this directly, as the format is subject to change
        without notice. Instead, use :func:`sitecustomize.environ.freeze`.


API Reference
-------------

"""

from __future__ import absolute_import

import logging
import os
import json


log = logging.getLogger(__name__)

VARIABLE_NAME = 'PYTHONENVIRONDIFF'

_dumps = json.dumps
_loads = json.loads


def _existing_diff(environ):
    blob = environ.get(VARIABLE_NAME)
    return _loads(blob) if blob else {}


def freeze(environ, names):
    """Flag the given names to reset to their current value in the next Python.
    
    :param dict environ: The environment that will be passed to the next Python.
    :param names: A list of variable names that should be reset to their current
        value (as in ``environ``) when the next sub-Python starts.
    
    This is useful to reset environment variables that are set by wrapper
    scripts that are nessesary to bootstrap the process, but we do not want to
    carry into any subprocess. E.g. ``LD_LIBRARY_PATH``.
    
    Usage::
    
        import os
        from subprocess import call
        
        from sitecustomize.environ import freeze
        
        env = dict(os.environ)
        env['DEMO'] = 'one'
        freeze(env, ('DEMO', ))
        env['DEMO'] = 'two'
        
        call(['python', '-c', 'import os; print os.environ["DEMO"]'], env=env)
        # Prints: one
        
    """
    diff = _existing_diff(environ)
    for name in names:
        diff[name] = environ.get(name)
    environ[VARIABLE_NAME] = _dumps(diff)


def apply_diff():
    blob = os.environ.pop(VARIABLE_NAME, None)
    diff = _loads(blob) if blob else {}
    if diff:
        for k, v in diff.iteritems():
            log.log(5, '%s="%s"', k, v)
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    else:
        log.log(5, 'nothing to apply')


def _setup():
    apply_diff()
