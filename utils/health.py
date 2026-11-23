from django.db import connection
from django.http import JsonResponse


def health(request):
    """GET /api/health/ — for uptime monitors (keeps a sleeping instance warm). Touches the database."""
    try:
        with connection.cursor() as c:
            c.execute('SELECT 1')
        db = True
    except Exception:
        db = False
    return JsonResponse({'status': 'ok' if db else 'degraded', 'db': db}, status=200 if db else 503)
