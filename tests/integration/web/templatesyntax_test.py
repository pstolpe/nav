"""Generates syntax tests for all NAV Django templates"""

import os
from os.path import join, relpath
from django.conf import settings
from django.template import loader
from django.template.loaders import app_directories

from nav.eventengine.alerts import (ensure_alert_templates_are_available,
                                    ALERT_TEMPLATE_DIR)
import pytest


def test_templates_can_be_found():
    templates = list(get_template_list())
    assert templates, "Can't find any Django templates"


def test_alert_templates_can_be_found():
    templates = list(get_template_list(ALERT_TEMPLATE_DIR))
    assert templates, "Can't find any Django alert message templates"


def get_template_list(directories=None):
    if not directories:
        ensure_alert_templates_are_available()
        directories = (settings.TEMPLATE_DIRS + get_nav_app_template_dirs())

    for tmpldir in directories:
        for dirname, _subdirs, files in os.walk(tmpldir):
            for name in files:
                fullpath = join(dirname, name)
                yield relpath(fullpath, tmpldir)


def get_nav_app_template_dirs():
    """
    This replaces django.template.loads.get_app_template_dirs, to just
    return templates that belong to apps in the nav namespace.
    """
    if hasattr(app_directories, 'app_template_dirs'):  # Django < 1.8
        return app_directories.app_template_dirs

    from django.apps import apps
    template_dirs = []
    for app_config in apps.get_app_configs():
        if not app_config.path or not app_config.name.startswith('nav.'):
            continue
        template_dir = os.path.join(app_config.path, 'templates')
        if os.path.isdir(template_dir):
            template_dirs.append(template_dir)

    # Immutable return value because it will be cached and shared by callers.
    return tuple(template_dirs)


@pytest.mark.parametrize("template_name", get_template_list())
def test_template_syntax(template_name):
    loader.get_template(template_name)
