import os


def save_uploaded_image(image_file, folder='uploads', filename_prefix='img', request=None):
    """
    Save an uploaded image (Cloudinary, or MEDIA_ROOT/<folder>/ in development — see utils/storage.py).
    Returns the value to store in the DB.
    """
    import time
    from utils import storage
    from utils.upload_security import checked_ext, random_token
    ext      = checked_ext(image_file, 'image')
    filename = f"{filename_prefix}_{int(time.time())}_{random_token()}{ext}"
    return storage.store(image_file, folder, filename, request)


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