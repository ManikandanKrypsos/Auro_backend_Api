import os


def save_uploaded_image(image_file, folder='uploads', filename_prefix='img', request=None):
    """
    Save uploaded image to MEDIA_ROOT/<folder>/
    Returns FULL URL string including domain.
    """
    from django.conf import settings
    import time

    upload_dir = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(upload_dir, exist_ok=True)

    ext      = os.path.splitext(image_file.name)[1].lower() or '.jpg'
    filename = f"{filename_prefix}_{int(time.time())}{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, 'wb+') as f:
        for chunk in image_file.chunks():
            f.write(chunk)

    # Build full URL
    relative_url = f"{settings.MEDIA_URL}{folder}/{filename}"

    if request:
        return request.build_absolute_uri(relative_url)

    # Fallback — use BASE_URL from settings or default
    base_url = getattr(settings, 'BASE_URL', 'https://auro-backend-api.onrender.com')
    return f"{base_url.rstrip('/')}{relative_url}"


def get_image_value(request, field_name, folder='uploads', prefix='img'):
    """
    Supports both file upload (multipart) and URL string.
    Priority: FILES > data string
    Returns full URL string to store in DB.
    """
    file = request.FILES.get(field_name)
    if file:
        try:
            return save_uploaded_image(file, folder=folder, filename_prefix=prefix, request=request)
        except Exception:
            return ''
    return request.data.get(field_name, '')