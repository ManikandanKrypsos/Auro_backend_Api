import os


def save_uploaded_image(image_file, folder='uploads', filename_prefix='img'):
    """
    Save uploaded image to MEDIA_ROOT/<folder>/
    Returns relative URL string.
    Accepts InMemoryUploadedFile from request.FILES
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

    return f"{settings.MEDIA_URL}{folder}/{filename}"


def get_image_value(request, field_name, folder='uploads', prefix='img'):
    """
    Supports both file upload (multipart) and URL string.
    Priority: FILES > data string
    Returns URL string to store in DB.
    """
    file = request.FILES.get(field_name)
    if file:
        try:
            return save_uploaded_image(file, folder=folder, filename_prefix=prefix)
        except Exception:
            return ''
    return request.data.get(field_name, '')