"""
In-app notifications (the bell). The app polls; nothing is pushed.

GET   /api/notifications/?is_read=false&type=leave_requested&page=1&page_size=20
GET   /api/notifications/unread-count/
PATCH /api/notifications/<id>/            {"is_read": true | false}
POST  /api/notifications/mark-all-read/   (optional {"type": "..."})
GET   /api/notifications/preferences/
PATCH /api/notifications/preferences/     {"leave_requested": false, ...}
"""
from django.core.paginator import Paginator
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsClinicStaff
from .models import Notification, NotificationPreference
from .service import TYPES, name_of


def _mine(request):
    return Notification.objects.filter(recipient_id=request.user.pk)


def _unread(request):
    return _mine(request).filter(is_read=False).count()


def serialize(n):
    data = {
        'id':         n.id,
        'type':       n.type,
        'message':    n.message,
        'ref':        n.ref or {},
        'actor':      {'id': n.actor_id, 'name': name_of(n.actor)} if n.actor_id else None,
        'is_read':    n.is_read,
        'read_at':    n.read_at,
        'created_at': n.created_at,
    }
    data.update(n.ref or {})          # leave_id / appointment_id / lead_id … also at the top level
    return data


class NotificationListView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request):
        p = request.query_params
        qs = _mine(request).select_related('actor')
        raw_read = str(p.get('is_read', '') or '').lower()
        if raw_read in ('true', 'false'):
            qs = qs.filter(is_read=(raw_read == 'true'))
        elif raw_read:
            return Response({'is_read': 'Use true or false.'}, status=400)
        if p.get('type'):
            types = [t.strip() for t in p['type'].split(',') if t.strip()]
            unknown = [t for t in types if t not in TYPES]
            if unknown:
                return Response({'type': f'Unknown type(s): {", ".join(unknown)}.'}, status=400)
            qs = qs.filter(type__in=types)
        errors, nums = {}, {}
        for name, default in (('page', 1), ('page_size', 20)):
            raw = str(p.get(name, '') or '').strip()
            if raw and (not raw.isdigit() or int(raw) < 1):
                errors[name] = 'Must be a whole number of 1 or more.'
            nums[name] = int(raw) if raw.isdigit() and int(raw) >= 1 else default
        if errors:
            return Response(errors, status=400)
        page_size = min(nums['page_size'], 100)
        paginator = Paginator(qs, page_size)
        page = paginator.get_page(nums['page'])
        return Response({
            'count':        paginator.count,
            'page':         page.number,
            'page_size':    page_size,
            'total_pages':  paginator.num_pages,
            'unread_count': _unread(request),
            'results':      [serialize(n) for n in page.object_list],
        })


class UnreadCountView(APIView):
    permission_classes = [IsClinicStaff]

    def get(self, request):
        return Response({'unread_count': _unread(request)})


class NotificationDetailView(APIView):
    permission_classes = [IsClinicStaff]

    def patch(self, request, pk):
        n = _mine(request).select_related('actor').filter(pk=pk).first()
        if not n:
            return Response({'error': 'Notification not found.'}, status=404)
        value = request.data.get('is_read', True)
        if value not in (True, False, 'true', 'false'):
            return Response({'is_read': 'Use true or false.'}, status=400)
        n.is_read = value in (True, 'true')
        n.read_at = timezone.now() if n.is_read else None
        n.save(update_fields=['is_read', 'read_at'])
        data = serialize(n)
        data['unread_count'] = _unread(request)
        return Response(data)


class MarkAllReadView(APIView):
    permission_classes = [IsClinicStaff]

    def post(self, request):
        qs = _mine(request).filter(is_read=False)
        type_ = request.data.get('type')
        if type_:
            if type_ not in TYPES:
                return Response({'type': 'Unknown notification type.'}, status=400)
            qs = qs.filter(type=type_)
        updated = qs.update(is_read=True, read_at=timezone.now())
        return Response({'updated': updated, 'unread_count': _unread(request)})


class PreferencesView(APIView):
    """Only the types that apply to the caller's role are listed. Default: all on."""
    permission_classes = [IsClinicStaff]

    def _payload(self, request):
        role = request.user.role
        off = set(NotificationPreference.objects.filter(user_id=request.user.pk, enabled=False)
                  .values_list('type', flat=True))
        return {'preferences': [
            {'type': t, 'label': label, 'description': desc, 'enabled': t not in off}
            for t, (label, desc, roles) in TYPES.items() if role in roles
        ]}

    def get(self, request):
        return Response(self._payload(request))

    def patch(self, request):
        data = request.data
        if isinstance(data, dict) and isinstance(data.get('preferences'), list):
            data = {str(x.get('type')): x.get('enabled') for x in data['preferences'] if isinstance(x, dict)}
        if not isinstance(data, dict) or not data:
            return Response({'error': 'Send {"<type>": true | false, …}.'}, status=400)
        allowed = {t for t, (_, _, roles) in TYPES.items() if request.user.role in roles}
        errors = {}
        for t, v in data.items():
            if t not in allowed:
                errors[t] = 'Unknown notification type for your role.'
            elif v not in (True, False):
                errors[t] = 'Use true or false.'
        if errors:
            return Response(errors, status=400)
        for t, v in data.items():
            NotificationPreference.objects.update_or_create(user_id=request.user.pk, type=t, defaults={'enabled': v})
        return Response(self._payload(request))
