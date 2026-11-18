"""
The clinic the current request belongs to. Set by the authentication classes from the
logged-in user (never from client input) and cleared by TenantContextMiddleware.
When no clinic is set (logins, webhooks, management commands, Celery), queries are unscoped.
"""
from contextvars import ContextVar

_current_clinic_id = ContextVar('current_clinic_id', default=None)


def get_current_clinic_id():
    return _current_clinic_id.get()


def set_current_clinic_id(clinic_id):
    _current_clinic_id.set(clinic_id)


def clear_current_clinic():
    _current_clinic_id.set(None)
