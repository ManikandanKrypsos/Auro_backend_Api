from .context import clear_current_clinic


class TenantContextMiddleware:
    """Starts and ends every request with no clinic selected (the auth class sets it)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        clear_current_clinic()
        try:
            return self.get_response(request)
        finally:
            clear_current_clinic()
