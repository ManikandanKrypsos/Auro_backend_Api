"""Opt-in page/page_size pagination shared by list endpoints."""
from django.core.paginator import Paginator
from rest_framework.response import Response

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def wants_pagination(request):
    return 'page' in request.query_params or 'page_size' in request.query_params


def paginate(request, queryset, serialize):
    """
    Without ?page / ?page_size → plain list (as before).
    With them → {count, page, page_size, total_pages, results}; page_size max 100.
    `serialize` turns a list of objects into a list of dicts.
    """
    if not wants_pagination(request):
        return Response(serialize(list(queryset)))
    errors = {}
    nums = {}
    for name, default in (('page', 1), ('page_size', DEFAULT_PAGE_SIZE)):
        raw = str(request.query_params.get(name, '') or '').strip()
        if not raw:
            nums[name] = default
        elif not raw.isdigit() or int(raw) < 1:
            errors[name] = 'Must be a whole number of 1 or more.'
        else:
            nums[name] = int(raw)
    if errors:
        return Response(errors, status=400)
    page_size = min(nums['page_size'], MAX_PAGE_SIZE)
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(nums['page'])
    return Response({
        'count':       paginator.count,
        'page':        page.number,
        'page_size':   page_size,
        'total_pages': paginator.num_pages,
        'results':     serialize(list(page.object_list)),
    })
