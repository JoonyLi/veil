from __future__ import unicode_literals, print_function, division
import os
from veil.backend.shell import *
from veil.backend.path import *
from veil.frontend.script import *

CURRENT_DIR = path(os.path.dirname(__file__))

@script('rebuild-index')
def rebuild_index():
    shell_execute('rm -rf ~/.PyCharm20/system/caches')
    shell_execute('rm -rf ~/.PyCharm20/system/index')


@script('patch-utrunner')
def patch_utrunner(pycharm_dir):
    build_txt = (path(pycharm_dir) / 'build.txt')
    if not build_txt.exists():
        raise Exception('please create link to pycharm under $VEIL_HOME/env')
    patched_utrunner_py = CURRENT_DIR / 'utrunner_py'
    utrunner_py = path(pycharm_dir) / 'helpers' / 'pycharm' / 'utrunner.py'
    shell_execute('cp {} {}'.format(patched_utrunner_py, utrunner_py))