"""Real WSGI/ORM runtime. Wrappers only count calls; no replaced decisions/data."""
import json
import os
from functools import wraps
from wsgiref.simple_server import make_server, WSGIRequestHandler

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
from django.conf import settings
from django.db import connection, connections
from authentication.views import MeView
from resources.views import ResourceViewSet
from integration import central_auth
from .authority import verify_principal

root = settings.ROOT
role = settings.DATABASES['default']['USER']
counts = {'sync_identity': 0, 'me': 0, 'list': 0, 'retrieve': 0, 'create': 0, 'partial_update': 0}


def observe(function, name):
    @wraps(function)
    def counted(*args, **kwargs):
        counts[name] += 1
        return function(*args, **kwargs)
    return counted


central_auth.sync_identity = observe(central_auth.sync_identity, 'sync_identity')
MeView.get = observe(MeView.get, 'me')
for action in ('list', 'retrieve', 'create', 'partial_update'):
    setattr(ResourceViewSet, action, observe(getattr(ResourceViewSet, action), action))


def observed(environ, start_response):
    connections.close_all()  # Each request really reconnects with fixed credentials.
    before = counts.copy()
    verbs = []

    def record(execute, sql, params, many, context):
        normalized = sql.strip().upper()
        assert not normalized.startswith(('SET ROLE', 'SET SESSION AUTHORIZATION'))
        verbs.append(normalized.split()[0])
        return execute(sql, params, many, context)

    with connection.execute_wrapper(record):
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_user, session_user, pg_backend_pid()')
            principal, session_user, pid = cursor.fetchone()
        response = application(environ, start_response)
    state = {'principal': principal, 'session_user': session_user, 'backend_pid': pid,
             'counts': counts.copy(), 'delta': {k: counts[k] - before[k] for k in counts},
             'sql_verbs': verbs, 'set_role': False}
    (root / ('state-' + role + '.json')).write_text(json.dumps(state))
    return response


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


verify_principal()
with make_server('127.0.0.1', 0, observed, handler_class=QuietHandler) as server:
    (root / ('ready-' + role + '.json')).write_text(json.dumps({'port': server.server_port}))
    server.serve_forever()
