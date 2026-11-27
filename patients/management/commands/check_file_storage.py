"""
python manage.py check_file_storage

Uploads a tiny PDF and image as private files and a public image, opens the signed / public links,
then deletes the test files. Run it once after setting CLOUDINARY_URL to confirm uploads work.
"""
import io
import urllib.request

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError

from utils import storage

PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
       b'\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa75\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82')
PDF = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n'


def _status(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=20) as r:
            return r.status
    except Exception as e:
        return getattr(e, 'code', str(e))


class Command(BaseCommand):
    help = 'Check that file uploads to Cloudinary work (private + public).'

    def handle(self, *args, **opts):
        if not storage.enabled():
            raise CommandError('CLOUDINARY_URL is not set — files are being saved on the server disk.')
        ok = True
        for folder, name, data, ctype in (('documents', '_check.pdf', PDF, 'application/pdf'),
                                          ('patients', '_check.png', PNG, 'image/png'),
                                          ('treatments', '_check.png', PNG, 'image/png')):
            ref = storage.store(SimpleUploadedFile(name, data, ctype), folder, name)
            link = storage.signed_url(ref)
            status = _status(link)
            raw = 'n/a'
            if storage.is_ref(ref):
                rt, pid, fmt = storage._split(ref)
                import cloudinary.utils
                plain = cloudinary.utils.cloudinary_url(pid, resource_type=rt, type='authenticated', format=fmt or None)[0]
                raw = _status(plain)           # must NOT open without a signature
            good = status == 200 and raw in ('n/a', 401, 403, 404)
            ok &= good
            self.stdout.write(f"{'OK ' if good else 'FAIL'} {folder:<11} stored={ref[:60]} link={status} unsigned={raw}")
            if storage.is_ref(ref):
                storage.delete(ref)
            else:
                import cloudinary.uploader
                cloudinary.uploader.destroy(f'{folder}/_check', invalidate=True)
        if not ok:
            raise CommandError('Some checks failed — see above. If only the PDF failed, enable '
                               '"Allow delivery of PDF and ZIP files" in Cloudinary Settings → Security.')
        self.stdout.write(self.style.SUCCESS('File storage works.'))
