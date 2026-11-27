"""
Request IDs and traceable access-denied responses.

Every response gets an X-Request-ID header (the caller's own X-Request-ID is reused when it looks
sane, otherwise a new one is made). Every log line written during the request carries the same id.

401 / 403 JSON responses are normalised to
    {"error": "<human-readable>", "code": "<stable code>", "request_id": "<id>", ...existing fields}
and logged (logger "aura.access") with user, role, clinic, method and path, so a request id
reported by the app can be looked up in the server logs.

Every other error (4xx / 5xx) with a JSON object body also gets "request_id". With DEBUG off, the
HTML 404 / 500 pages Django would return for /api/ paths become JSON
    {"error": ..., "code": "not_found" | "server_error", "request_id": ...}.

Timing: every response carries a Server-Timing header — total time, database time and the number
of queries — and requests slower than SLOW_REQUEST_MS (default 1000) are logged by "aura.perf".
"""
import contextvars
import json
import logging
import os
import re
import time
import uuid

from django.conf import settings
from django.db import connection

_request_id = contextvars.ContextVar('aura_request_id', default='-')
_SAFE_ID = re.compile(r'^[A-Za-z0-9._-]{8,64}$')
log = logging.getLogger('aura.access')
perf_log = logging.getLogger('aura.perf')
SLOW_REQUEST_MS = int(os.environ.get('SLOW_REQUEST_MS', '1000'))

ROLE_LABELS = {'admin': 'Admin', 'reception': 'Receptionist', 'therapist': 'Therapist'}
DRF_DEFAULT_DENIED = 'You do not have permission to perform this action.'


def get_request_id():
    return _request_id.get()


class RequestIDLogFilter(logging.Filter):
    def filter(self, record):
        record.request_id = _request_id.get()
        return True


def _user_info(request):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        user = getattr(request, 'denied_user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        return None, '', None
    return getattr(user, 'pk', None), getattr(user, 'role', '') or '', getattr(user, 'clinic_id', None)


class _QueryStats:
    """Counts database queries and their time during one request (connection.execute_wrapper)."""
    def __init__(self):
        self.count, self.ms = 0, 0.0

    def __call__(self, execute, sql, params, many, context):
        t = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            self.count += 1
            self.ms += (time.perf_counter() - t) * 1000


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get('HTTP_X_REQUEST_ID', '')
        rid = incoming if _SAFE_ID.match(incoming or '') else uuid.uuid4().hex
        # Not reset at the end: Django logs 4xx/5xx after the middleware has returned, and those
        # lines should still carry this id. The next request on this thread sets its own.
        _request_id.set(rid)
        request.request_id = rid
        stats = _QueryStats()
        started = time.perf_counter()
        with connection.execute_wrapper(stats):
            response = self.get_response(request)
        total_ms = (time.perf_counter() - started) * 1000
        if response.status_code in (401, 403):
            self._annotate_denied(request, response, rid)
        elif response.status_code >= 400:
            self._annotate_error(request, response, rid)
        response['X-Request-ID'] = rid
        response['Server-Timing'] = (f'app;dur={total_ms:.0f}, '
                                     f'db;dur={stats.ms:.0f};desc="{stats.count} queries"')
        if total_ms >= SLOW_REQUEST_MS and not request.path.startswith(('/static/', '/media/')):
            user_id, role, clinic_id = _user_info(request)
            perf_log.warning('slow %s %s -> %s in %.0fms (db %.0fms, %d queries) user=%s role=%s clinic=%s',
                             request.method, request.get_full_path()[:200], response.status_code, total_ms,
                             stats.ms, stats.count, user_id, role or '-', clinic_id)
        return response

    @staticmethod
    def _json_body(response):
        if 'json' not in (response.get('Content-Type') or '') or getattr(response, 'streaming', False):
            return None
        try:
            return json.loads(response.content or b'{}')
        except (ValueError, UnicodeDecodeError):
            return None

    @staticmethod
    def _set_body(response, body):
        response.content = json.dumps(body).encode('utf-8')
        response['Content-Type'] = 'application/json'
        if response.has_header('Content-Length'):
            response['Content-Length'] = str(len(response.content))

    def _annotate_error(self, request, response, rid):
        """request_id on every JSON error; JSON instead of Django's HTML 404 / 500 pages for the API."""
        body = self._json_body(response)
        if isinstance(body, dict):
            if 'request_id' not in body:
                body['request_id'] = rid
                self._set_body(response, body)
            return
        if body is None and not settings.DEBUG and request.path.startswith('/api/') \
                and response.status_code in (404, 500, 502, 503):
            if response.status_code == 404:
                body = {'error': 'Not found.', 'code': 'not_found'}
            else:
                body = {'error': 'Something went wrong on our side. Please try again; if it keeps happening, '
                                 'send us this request id.', 'code': 'server_error'}
            body.update(fields={}, request_id=rid)
            self._set_body(response, body)

    def _annotate_denied(self, request, response, rid):
        user_id, role, clinic_id = _user_info(request)
        code = None
        if 'json' in (response.get('Content-Type') or '') and not getattr(response, 'streaming', False):
            try:
                body = json.loads(response.content or b'{}')
            except (ValueError, UnicodeDecodeError):
                body = None
            if isinstance(body, dict):
                detail = body.get('detail')
                if response.status_code == 401:
                    body.setdefault('code', 'not_authenticated')
                    body.setdefault('error', str(detail) if detail else 'Please log in again.')
                else:
                    body.setdefault('code', 'not_permitted')
                    if 'error' not in body:
                        if not detail or str(detail) == DRF_DEFAULT_DENIED:
                            who = ROLE_LABELS.get(role)
                            body['error'] = (f"Your role ({who}) doesn't have access to this." if who
                                             else "You don't have access to this.")
                        else:
                            body['error'] = str(detail)
                body['request_id'] = rid
                code = body['code']
                response.content = json.dumps(body).encode('utf-8')
                if response.has_header('Content-Length'):
                    response['Content-Length'] = str(len(response.content))
        log.warning('%s %s %s %s user=%s role=%s clinic=%s', response.status_code, code or '-',
                    request.method, request.path, user_id, role or '-', clinic_id)
