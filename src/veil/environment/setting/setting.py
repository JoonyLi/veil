from __future__ import unicode_literals, print_function, division
import sys
from veil.model.collection import *
from veil.environment import *

initialized = False
settings = {}
coordinators = []


def add_settings(additional_settings, overrides=False):
    global settings
    if initialized:
        raise Exception('settings has already been initialized: {}'.format(settings))
    settings = merge_settings(settings, additional_settings, overrides=overrides)
    return settings


def register_settings_coordinator(coordinator):
    coordinators.append(coordinator)


def get_settings():
    global initialized
    global settings
    if not initialized:
        initialized = True
        settings = merge_settings(settings, get_application_settings())
    for coordinator in coordinators:
        settings = coordinator(settings)
        if not isinstance(settings, DictObject):
            raise Exception('{} should return DictObject'.format(coordinator))
    return settings


def merge_multiple_settings(*multiple_settings):
    merged_settings = {}
    for settings in multiple_settings:
        merged_settings = merge_settings(merged_settings, settings)
    return merged_settings


def merge_settings(base, updates, overrides=False):
    if base is None:
        return updates
    if isinstance(base, dict) and isinstance(updates, dict):
        updated = DictObject()
        for k, v in base.items():
            try:
                updated[k] = merge_settings(v, updates.get(k), overrides=overrides)
            except:
                raise Exception('can not merge: {}\r\n{}'.format(k, sys.exc_info()[1]))
        for k, v in updates.items():
            if k not in updated:
                updated[k] = v
        return updated
    if base == updates:
        return base
    if updates is not None:
        if overrides:
            return updates
        else:
            raise Exception('can not merge {} with {}'.format(base, updates))
    return base


def load_config_from(path, *expected_keys):
    config = DictObject()
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line:
            key, value = line.split('=')
            config[key] = value
    assert set(expected_keys) == set(config.keys()),\
    'config file {} does not provide exact keys we want, expected: {}, actual: {}'.format(
        path, expected_keys, config.keys())
    return config