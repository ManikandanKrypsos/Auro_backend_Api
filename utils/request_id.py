"""
Request IDs and traceable access-denied responses.

Every response gets an X-Request-ID header (the caller's own X-Request-ID is reused when it looks
sane, otherwise a new one is made). Every log line written during the request carries the same id.

401 / 403 JSON responses are normalised to
    {"error": "<human-readable>", "code": "<stable code>", "request_id": "<id>", ...existing fields}
and logged (logger "aura.access") with user, role, clinic, method and path, so a request id
reported by the app can be looked up in the server logs.
"""
import contextvars
import json
import logging
import re
import uuid

_request_id = contextvars.ContextVar('aura_request_id', default='-')
_SAFE_ID = re.compile(r'^[A-Za-z0-9._-]{8,64}$')
log = logging.getLogger('aura.access')

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
        response = self.get_response(request)
        if response.status_code in (401, 403):
            self._annotate_denied(request, response, rid)
        response['X-Request-ID'] = rid
        return response

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
