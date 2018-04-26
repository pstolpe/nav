from __future__ import print_function
import datetime
import os
import io
import re
import shlex
import subprocess

import pytest
from django.test import Client

gunicorn = None

########################################################################
#                                                                      #
# Set up the required components for an integration test. Components   #
# such as PostgreSQL and Apache are assumed to already be installed on #
# the system. The system is assumed to be Debian. See                  #
# tests/docker/Dockerfile.                                             #
#                                                                      #
########################################################################

if os.environ.get('WORKSPACE'):
    SCRIPT_PATH = os.path.join(os.environ['WORKSPACE'], 'tests/docker/scripts')
else:
    SCRIPT_PATH = '/'
SCRIPT_CREATE_DB = os.path.join(SCRIPT_PATH, 'create-db.sh')


def pytest_configure(config):
    subprocess.check_call([SCRIPT_CREATE_DB])
    os.environ['TARGETURL'] = "http://localhost:8000/"
    start_gunicorn()

    from nav.bootstrap import bootstrap_django
    bootstrap_django('pytest')
    from django.test.utils import setup_test_environment
    setup_test_environment()


def pytest_unconfigure(config):
    stop_gunicorn()


def start_gunicorn():
    global gunicorn
    workspace = os.path.join(os.environ.get('WORKSPACE', ''), 'reports')
    errorlog = os.path.join(workspace, 'gunicorn-error.log')
    accesslog = os.path.join(workspace, 'gunicorn-access.log')
    gunicorn = subprocess.Popen(['gunicorn',
                                 '--error-logfile', errorlog,
                                 '--access-logfile', accesslog,
                                 'navtest_wsgi:application'])


def stop_gunicorn():
    if gunicorn:
        gunicorn.terminate()


########################################################################
#                                                                      #
# All to do with discovering all NAV binaries and building fixtures to #
# generate tests for each of them                                      #
#                                                                      #
########################################################################
TESTARGS_PATTERN = re.compile(
    r'^# +-\*-\s*testargs:\s*(?P<args>.*?)\s*(-\*-)?\s*$',
    re.MULTILINE)
NOTEST_PATTERN = re.compile(
    r'^# +-\*-\s*notest\s*(-\*-)?\s*$', re.MULTILINE)
BINDIR = './bin'


def pytest_generate_tests(metafunc):
    if 'binary' in metafunc.fixturenames:
        binaries = _nav_binary_tests()
        ids = [b[0] for b in binaries]
        metafunc.parametrize("binary", _nav_binary_tests(), ids=ids)


def _nav_binary_tests():
    for binary in _nav_binary_list():
        for args in _scan_testargs(binary):
            if args:
                yield args


def _nav_binary_list():
    files = sorted(os.path.join(BINDIR, f)
                   for f in os.listdir(BINDIR)
                   if not _is_excluded(f))
    return (f for f in files if os.path.isfile(f))


def _is_excluded(filename):
    return (filename.endswith('~') or filename.startswith('.') or
            filename.startswith('Makefile'))


def _scan_testargs(filename):
    """
    Scans filename for testargs comments and returns a list of elements
    suitable for invocation of this binary with the given testargs
    """
    print("Getting test args from {}".format(filename))
    contents = io.open(filename, encoding="utf-8").read()
    matches = TESTARGS_PATTERN.findall(contents)
    if matches:
        retval = []
        for testargs, _ in matches:
            testargs = shlex.split(testargs)
            retval.append([filename] + testargs)
        return retval
    else:
        matches = NOTEST_PATTERN.search(contents)
        if not matches:
            return [[filename]]
        else:
            return []

##################
#                #
# Other fixtures #
#                #
##################

@pytest.fixture()
def localhost():
    from nav.models.manage import Netbox
    box = Netbox(ip='127.0.0.1', sysname='localhost.example.org',
                 organization_id='myorg', room_id='myroom', category_id='SRV',
                 read_only='public', snmp_version=2)
    box.save()
    yield box
    print("teardown test device")
    box.delete()


@pytest.fixture()
def serializer_models():
    """Fixture for testing API serializers

    - unrecognized_neighbor
    - auditlog
    """
    from nav.models import cabling, event, manage, profiles, rack
    from nav.auditlog import models as auditlog
    netbox = manage.Netbox(ip='127.0.0.1', sysname='localhost.example.org',
                           organization_id='myorg', room_id='myroom', category_id='SRV',
                           read_only='public', snmp_version=2)
    netbox.save()
    interface = manage.Interface(netbox=netbox, ifindex=1, ifname='if1',
                                 ifdescr='ifdescr', iftype=1, speed=10)
    interface.save()
    manage.Cam(sysname='asd', mac='aa:aa:aa:aa:aa:aa', ifindex=1,
               end_time=datetime.datetime.now()).save()
    manage.Arp(sysname='asd', mac='aa:bb:cc:dd:ee:ff', ip='123.123.123.123',
               end_time=datetime.datetime.now()).save()
    manage.Prefix(net_address='123.123.123.123').save()
    manage.Vlan(vlan=10, net_type_id='lan').save()
    rack.Rack(room_id='myroom').save()
    cabel = cabling.Cabling(room_id='myroom', jack='1')
    cabel.save()
    cabling.Patch(interface=interface, cabling=cabel).save()

    source = event.Subsystem.objects.get(pk='pping')
    target = event.Subsystem.objects.get(pk='eventEngine')
    event_type = event.EventType.objects.get(pk='boxState')

    event.EventQueue(source=source, target=target, event_type=event_type, netbox=netbox).save()
    admin = profiles.Account.objects.get(login='admin')
    auditlog.LogEntry.add_log_entry(admin, verb='verb', template='asd')


@pytest.fixture(scope='session')
def client():
    """Provides a Django test Client object already logged in to the web UI as
    an admin"""
    from django.core.urlresolvers import reverse

    client_ = Client()
    url = reverse('webfront-login')
    username = os.environ.get('ADMINUSERNAME', 'admin')
    password = os.environ.get('ADMINPASSWORD', 'admin')
    client_.post(url, {'username': username,
                       'password': password})
    return client_


@pytest.fixture(scope='function')
def db(request):
    """Ensures db modifications are rolled back after the test ends.

    This is done by disabling transaction management, running everything
    inside a transaction that is rolled back after the test is done.
    Effectively, it reuses the functionality of Django's own TestCase
    implementation, just fitted for pytest.

    This idea is entirely lifted from pytest-django; we can't use
    pytest-django directly, yet, because it won't work on Django 1.7 (and NAV
    has fairly non-standard use of Django, anyway)

    """
    if _is_django_unittest(request):
        return

    from nav.tests.cases import DjangoTransactionTestCase as django_case

    test_case = django_case(methodName='__init__')
    test_case._pre_setup()
    request.addfinalizer(test_case._post_teardown)


def _is_django_unittest(request_or_item):
    """Returns True if the request_or_item is a Django test case, otherwise
    False
    """
    from django.test import SimpleTestCase

    cls = getattr(request_or_item, 'cls', None)

    if cls is None:
        return False

    return issubclass(cls, SimpleTestCase)


@pytest.fixture(scope='function')
def token():
    """Creates a write enabled token for API access but without endpoints

    Tests should manipulate the endpoints as they see fit.
    """
    from nav.models.api import APIToken
    from datetime import datetime, timedelta

    token = APIToken(token='xxxxxx',
                     expires=datetime.now() + timedelta(days=1),
                     client_id=1,
                     permission='write')
    token.save()
    return token


@pytest.fixture(scope='function')
def api_client(token):
    """Creates a client for API access"""

    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.token)
    return client
