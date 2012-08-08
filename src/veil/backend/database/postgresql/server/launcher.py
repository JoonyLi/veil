from __future__ import unicode_literals, print_function, division
import contextlib
import time
from veil.frontend.cli import *
from veil.backend.shell import *
from veil.environment.deployment import *

@deployment_script('up')
def bring_up_postgresql_server():
    settings = get_deployment_settings()
    pass_control_to('postgres -D {}'.format(settings.postgresql.data_directory))


@deployment_script('down')
def bring_down_postgresql_server():
    settings = get_deployment_settings()
    shell_execute('su {} -c "pg_ctl -D {} stop"'.format(
        settings.postgresql.owner,
        settings.postgresql.data_directory))


@contextlib.contextmanager
def postgresql_server_running():
    settings = get_deployment_settings()
    shell_execute('su {} -c "pg_ctl -D {} start"'.format(
        settings.postgresql.owner,
        settings.postgresql.data_directory))
    time.sleep(5)
    yield
    bring_down_postgresql_server()