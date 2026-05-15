import os
import requests as req
from django.conf import settings


def safe_image_url(url, request=None):
    """
    Returns the URL only if it's valid and accessible.
    - If URL is None or empty → return None
    - If URL is an external URL (http/https not on our domain) → return as-is
    - If URL is a local media path → check if file exists on disk
    - If file doesn't exist → return None
    """
    if not url:
        return None

    # External URL (Unsplash, CDN, etc.) — return as-is, don't validate
    our_domain = getattr(settings, 'ALLOWED_HOSTS', [])
    render_domain = 'auro-backend-api.onrender.com'

    if url.startswith('http'):
        # If it's our own server URL, check file on disk
        if render_domain in url or any(h in url for h in our_domain if h not in ['*', 'localhost']):
            # Extract relative path and check if file exists
            try:
                # Convert URL to file path
                media_url = settings.MEDIA_URL  # e.g. /media/
                if media_url in url:
                    relative = url.split(media_url, 1)[1]  # e.g. patients/patient_49.jpg
                    abs_path = os.path.join(settings.MEDIA_ROOT, relative)
                    if not os.path.exists(abs_path):
                        return None
            except Exception:
                pass
        return url

    # Relative path — check if file exists
    try:
        abs_path = os.path.join(settings.MEDIA_ROOT, url.lstrip('/'))
        if not os.path.exists(abs_path):
            return None
        if request:
            return request.build_absolute_uri(settings.MEDIA_URL + url.lstrip('/'))
    except Exception:
        return None

    return url