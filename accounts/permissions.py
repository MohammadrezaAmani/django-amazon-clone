from rest_framework import permissions


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to create, update, and delete objects.
    Read-only access is allowed for other users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission to only allow verified users to access the view.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_verified


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """

    def has_object_permission(self, request, view, obj):  # type: ignore
        if request.user and request.user.is_staff:
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user

        if hasattr(obj, "owner"):
            return obj.owner == request.user

        if hasattr(obj, "id") and hasattr(request.user, "id"):
            return obj.id == request.user.id

        return False
