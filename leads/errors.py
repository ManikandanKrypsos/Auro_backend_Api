"""Leads use the shared error shape (utils/api_errors.py)."""
from utils.api_errors import error, validation_error  # noqa: F401


def lead_not_found():
    return error(404, 'lead_not_found', 'Lead not found.')
