"""
Stored file references ("cld://...") ⇄ temporary signed links, applied to every API response and
request body so no view or serializer has to know about it (see utils.storage).
"""
from django.http import QueryDict
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer

from . import storage


def _walk(value, fn):
    if isinstance(value, str):
        return fn(value)
    if isinstance(value, dict):
        return {k: _walk(v, fn) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_walk(v, fn) for v in value]
    return value


def signed(data):
    """Replace every stored file reference in a response with a signed link."""
    if not storage.enabled():
        return data
    return _walk(data, storage.signed_url)


class SignedFileJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return super().render(signed(data), accepted_media_type, renderer_context)


def _unsign_querydict(q):
    out = QueryDict(mutable=True)
    for key, values in q.lists():
        out.setlist(key, [storage.to_ref(v) for v in values])
    out._mutable = False
    return out


class UnsigningJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        data = super().parse(stream, media_type, parser_context)
        return _walk(data, storage.to_ref) if storage.enabled() else data


class UnsigningFormParser(FormParser):
    def parse(self, stream, media_type=None, parser_context=None):
        data = super().parse(stream, media_type, parser_context)
        return _unsign_querydict(data) if storage.enabled() else data


class UnsigningMultiPartParser(MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(stream, media_type, parser_context)
        if storage.enabled():
            result.data = _unsign_querydict(result.data)
        return result
