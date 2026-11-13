"""
Validation for every file upload: allowed types only, size limit, real content
check, and an unguessable filename.
"""
import os
import uuid
from rest_framework.exceptions import ValidationError

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.heic', '.heif'}
DOC_EXTS   = IMAGE_EXTS | {'.pdf'}
MAX_BYTES  = 10 * 1024 * 1024


def checked_ext(upload, kind='image', default='.jpg'):
    """Return the file extension if the upload is allowed; raise 400 otherwise."""
    ext     = os.path.splitext(upload.name or '')[1].lower() or default
    allowed = DOC_EXTS if kind == 'document' else IMAGE_EXTS
    if ext not in allowed:
        raise ValidationError({'file': f"File type '{ext}' is not allowed. Allowed: {', '.join(sorted(allowed))}."})
    if upload.size and upload.size > MAX_BYTES:
        raise ValidationError({'file': 'File is too large (max 10 MB).'})

    head = upload.read(16)
    upload.seek(0)
    if ext == '.pdf':
        ok = head.startswith(b'%PDF')
    elif ext in ('.heic', '.heif'):
        ok = b'ftyp' in head
    else:
        try:
            from PIL import Image
            Image.open(upload).verify()
            ok = True
        except Exception:
            ok = False
        upload.seek(0)
    if not ok:
        raise ValidationError({'file': 'The file content does not match its type.'})
    return ext


def random_token():
    """Unguessable filename part."""
    return uuid.uuid4().hex[:16]
