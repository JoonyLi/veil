from __future__ import unicode_literals, print_function, division
from veil_installer import *
from veil.environment import *
from veil.model.collection import *
from veil.environment.setting import *
from veil.development.test import *
from veil.frontend.template import *

overriden_website_configs = {}

@composite_installer('website')
@using_isolated_template
def install_website(purpose, config):
    resources = list(BASIC_LAYOUT_RESOURCES)
    resources.append(file_resource(VEIL_ETC_DIR / '{}-website.cfg'.format(purpose), content=get_template(
        'website.cfg.j2').render(config=config)))
    return [], resources


def load_website_config(purpose):
    try:
        config = load_config_from(VEIL_ETC_DIR / '{}-website.cfg'.format(purpose),
            'domain', 'domain_port', 'host', 'port', 'secure_cookie_salt', 'master_template_directory',
            'prevents_xsrf', 'recalculates_static_file_hash', 'clears_template_cache')
        config.port = int(config.port)
        config.prevents_xsrf = unicode(True) == config.prevents_xsrf
        config.recalculates_static_file_hash = unicode(True) == config.recalculates_static_file_hash
        config.clears_template_cache = unicode(True) == config.clears_template_cache
    except IOError, e:
        if 'test' == VEIL_SERVER:
            config = DictObject()
        else:
            raise
    if 'test' == VEIL_SERVER:
        config.update(overriden_website_configs.get(purpose, {}))
    return config


def override_website_config(purpose, **overrides):
    get_executing_test().addCleanup(overriden_website_configs.clear)
    overriden_website_configs.setdefault(purpose, {}).update(overrides)


def get_website_url_prefix(purpose):
    config = load_website_config(purpose)
    return 'http://{}:{}'.format(config.domain, config.domain_port)