from __future__ import unicode_literals, print_function, division
from veil.environment.installation import *

__import__('veil.supervisor')
__import__('demo.website')

@installation_script()
def install_demo():
    pass
