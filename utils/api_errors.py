"""
One error shape for API endpoints (leads, invoices, payments):

    {"error": "<human-readable>", "code": "<stable code>", "fields": {"<field>": "<message>"}, "request_id": "…"}

`fields` is {} unless specific input fields were wrong. 401/403 come from the shared access-denied
handling and have the same error / code / request_id keys.
"""
from rest_framework.response import Response

from utils.request_id import get_request_id


def error(status, code, message, fields=None, **extra):
    body = {'error': message, 'code': code, 'fields': fields or {}, 'request_id': get_request_id()}
    body.update(extra)
    return Response(body, status=status)


def _first(msgs):
    if isinstance(msgs, (list, tuple)):
        return str(msgs[0]) if msgs else ''
    if isinstance(msgs, dict):
        return _first(next(iter(msgs.values()), ''))
    return str(msgs)


def validation_error(errors, message=None):
    """DRF serializer.errors (or a plain {field: message}) → the standard 400."""
    fields = {k: _first(v) for k, v in dict(errors).items()}
    if not message:
        k, v = next(iter(fields.items()), ('', 'Invalid input.'))
        message = v if k in ('', 'non_field_errors') else f'{k}: {v}'
    return error(400, 'validation_error', message, fields)
