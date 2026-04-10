from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsAdminOrReception(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'reception']

class IsTherapist(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'therapist'

class IsAdminOrReadOnly(BasePermission):
    """Anyone logged in can read. Only admin can write."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.role == 'admin'