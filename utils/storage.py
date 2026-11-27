"""
Where uploaded files live.

With the four R2_* environment variables set, uploads go to a PRIVATE Cloudflare R2 bucket
(S3-compatible). The database stores a reference like "r2://consent_forms/consent_12_ab12.pdf" — never
a public URL. Every API response turns those references into short-lived signed links
(utils.file_refs.SignedFileJSONRenderer), so only logged-in staff who can see the record can open the
file, and a copied link stops working after FILE_URL_TTL seconds.

Without R2 (local development) files are written to MEDIA_ROOT as before and the stored value is
the absolute /media/ URL.

Env:  R2_ENDPOINT_URL      https://<account_id>.eu.r2.cloudflarestorage.com   (EU jurisdiction bucket)
      R2_ACCESS_KEY_ID
      R2_SECRET_ACCESS_KEY
      R2_BUCKET            e.g. aura-files
      FILE_URL_TTL         optional, seconds a signed link stays valid (default 3600)
"""
import mimetypes
import os
from functools import lru_cache
from urllib.parse import unquote, urlsplit

from django.conf import settings

PREFIX = 'r2://'


def enabled():
    return bool(getattr(settings, 'R2_BUCKET', '') and getattr(settings, 'R2_ENDPOINT_URL', '')
                and getattr(settings, 'R2_ACCESS_KEY_ID', '') and getattr(settings, 'R2_SECRET_ACCESS_KEY', ''))


@lru_cache(maxsize=1)
def _client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name='auto',
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'},
                      retries={'max_attempts': 3, 'mode': 'standard'}),
    )


def is_ref(value):
    return isinstance(value, str) and value.startswith(PREFIX)


def store(upload, folder, filename, request=None):
    """
    Save an uploaded file (already validated with utils.upload_security.checked_ext).
    Returns the value to keep in the database: "r2://<folder>/<filename>" with R2,
    otherwise the absolute local /media/ URL (development).
    """
    key = f'{folder.strip("/")}/{filename}'
    if enabled():
        upload.seek(0)
        content_type = getattr(upload, 'content_type', None) or mimetypes.guess_type(filename)[0] \
            or 'application/octet-stream'
        _client().upload_fileobj(upload, settings.R2_BUCKET, key, ExtraArgs={'ContentType': content_type})
        return PREFIX + key
    path = os.path.join(settings.MEDIA_ROOT, folder.strip('/'))
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, filename), 'wb+') as f:
        for chunk in upload.chunks():
            f.write(chunk)
    relative = f'{settings.MEDIA_URL}{key}'
    if request is not None:
        return request.build_absolute_uri(relative)
    return f"{getattr(settings, 'BASE_URL', 'https://auro-backend-api.onrender.com').rstrip('/')}{relative}"


def signed_url(ref, ttl=None):
    """A temporary link for a stored reference (non-references are returned unchanged)."""
    if not is_ref(ref) or not enabled():
        return ref
    return _client().generate_presigned_url(
        'get_object', Params={'Bucket': settings.R2_BUCKET, 'Key': ref[len(PREFIX):]},
        ExpiresIn=ttl or int(getattr(settings, 'FILE_URL_TTL', 3600)),
    )


def to_ref(value):
    """
    The reverse of signed_url: a signed link the app sent back (e.g. a form re-submitting the
    image it was shown) becomes the stored reference again, so expiring links are never saved.
    """
    if not isinstance(value, str) or not enabled() or not value.startswith(('http://', 'https://')):
        return value
    base = urlsplit(settings.R2_ENDPOINT_URL.rstrip('/'))
    u = urlsplit(value)
    prefix = f'/{settings.R2_BUCKET}/'
    if u.netloc == base.netloc and u.path.startswith(prefix):
        return PREFIX + unquote(u.path[len(prefix):])
    return value


def delete(ref):
    """Best-effort removal of a stored file (R2 or local)."""
    try:
        if is_ref(ref) and enabled():
            _client().delete_object(Bucket=settings.R2_BUCKET, Key=ref[len(PREFIX):])
        elif isinstance(ref, str) and settings.MEDIA_URL in ref:
            path = os.path.join(settings.MEDIA_ROOT, ref.split(settings.MEDIA_URL, 1)[1])
            if os.path.isfile(path):
                os.remove(path)
    except Exception:
        pass
