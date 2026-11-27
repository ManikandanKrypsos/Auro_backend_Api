"""
Where uploaded files live.

With CLOUDINARY_URL set (cloudinary://<api_key>:<api_secret>@<cloud_name>), uploads go to Cloudinary:

- Patient data — patient photos, session photos, consent forms, documents (PRIVATE_FOLDERS) — is
  uploaded as type "authenticated": it can't be opened by a plain URL. The database stores a
  reference like "cld://raw/documents/doc_12_ab12.pdf" or "cld://image/patients/patient_7_cd34.jpg",
  and every API response turns it into a signed download link that expires after FILE_URL_TTL
  seconds (utils.file_refs.SignedFileJSONRenderer).
- Everything else (treatment pictures, staff photos) is a normal public Cloudinary image URL.
- PDFs are stored as "raw" files, images as "image".

Without CLOUDINARY_URL (local development) files are written to MEDIA_ROOT as before and the stored
value is the absolute /media/ URL.

Check a live setup with:  python manage.py check_file_storage
"""
import os
import time
from urllib.parse import parse_qs, urlsplit

from django.conf import settings

PREFIX = 'cld://'
PRIVATE_FOLDERS = {'patients', 'session_photos', 'consent_forms', 'documents'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.heif'}


def enabled():
    return bool(os.environ.get('CLOUDINARY_URL') or getattr(settings, 'CLOUDINARY_URL', ''))


def _cloudinary():
    """The SDK reads CLOUDINARY_URL from the environment."""
    import cloudinary
    if not cloudinary.config().api_secret:
        url = getattr(settings, 'CLOUDINARY_URL', '')
        if url and not os.environ.get('CLOUDINARY_URL'):
            os.environ['CLOUDINARY_URL'] = url
        cloudinary.reset_config()
    cloudinary.config(secure=True)
    return cloudinary


def is_ref(value):
    return isinstance(value, str) and value.startswith(PREFIX)


def _split(ref):
    """'cld://image/patients/p_1.jpg' → ('image', 'patients/p_1', 'jpg'); raw keeps the extension in the id."""
    resource_type, _, rest = ref[len(PREFIX):].partition('/')
    if resource_type == 'raw':
        return resource_type, rest, ''
    base, ext = os.path.splitext(rest)
    return resource_type, base, ext.lstrip('.')


def store(upload, folder, filename, request=None):
    """
    Save an uploaded file (already validated with utils.upload_security.checked_ext).
    Returns the value to keep in the database (see module doc).
    """
    folder = folder.strip('/')
    if enabled():
        cld = _cloudinary()
        import cloudinary.uploader
        base, ext = os.path.splitext(filename)
        is_image = ext.lower() in IMAGE_EXTS
        private = folder in PRIVATE_FOLDERS
        upload.seek(0)
        result = cloudinary.uploader.upload(
            upload,
            public_id=f'{folder}/{base if is_image else filename}',
            resource_type='image' if is_image else 'raw',
            type='authenticated' if private else 'upload',
            overwrite=False,
        )
        if not private:
            return result['secure_url']
        if is_image:
            return f"{PREFIX}image/{result['public_id']}.{result.get('format') or ext.lstrip('.')}"
        return f"{PREFIX}raw/{result['public_id']}"
    path = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, filename), 'wb+') as f:
        for chunk in upload.chunks():
            f.write(chunk)
    relative = f'{settings.MEDIA_URL}{folder}/{filename}'
    if request is not None:
        return request.build_absolute_uri(relative)
    return f"{getattr(settings, 'BASE_URL', 'https://auro-backend-api.onrender.com').rstrip('/')}{relative}"


def signed_url(ref, ttl=None):
    """A temporary link for a stored reference (anything else is returned unchanged)."""
    if not is_ref(ref) or not enabled():
        return ref
    _cloudinary()
    import cloudinary.utils
    resource_type, public_id, fmt = _split(ref)
    return cloudinary.utils.private_download_url(
        public_id, fmt, resource_type=resource_type, type='authenticated',
        expires_at=int(time.time()) + (ttl or int(getattr(settings, 'FILE_URL_TTL', 3600))),
    )


def to_ref(value):
    """
    The reverse of signed_url: a signed link the app sent back (e.g. a form re-submitting the
    image it was shown) becomes the stored reference again, so expiring links are never saved.
    """
    if not isinstance(value, str) or not enabled() or '/download?' not in value:
        return value
    u = urlsplit(value)
    if not u.netloc.endswith('cloudinary.com'):
        return value
    parts = u.path.strip('/').split('/')           # v1_1/<cloud>/<resource_type>/download
    q = parse_qs(u.query)
    if len(parts) < 4 or parts[-1] != 'download' or 'public_id' not in q:
        return value
    resource_type, public_id = parts[-2], q['public_id'][0]
    fmt = (q.get('format') or [''])[0]
    return f'{PREFIX}{resource_type}/{public_id}' + (f'.{fmt}' if fmt and resource_type != 'raw' else '')


def delete(ref):
    """Best-effort removal of a stored private file (Cloudinary or local)."""
    try:
        if is_ref(ref) and enabled():
            _cloudinary()
            import cloudinary.uploader
            resource_type, public_id, _ = _split(ref)
            cloudinary.uploader.destroy(public_id, resource_type=resource_type, type='authenticated', invalidate=True)
        elif isinstance(ref, str) and settings.MEDIA_URL in ref and not ref.startswith('https://res.cloudinary.com'):
            path = os.path.join(settings.MEDIA_ROOT, ref.split(settings.MEDIA_URL, 1)[1])
            if os.path.isfile(path):
                os.remove(path)
    except Exception:
        pass
