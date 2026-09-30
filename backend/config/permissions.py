from rest_framework.permissions import BasePermission


def permission_required(code):
    class _Required(BasePermission):
        message = "没有权限"

        def has_permission(self, request, view):
            user = request.user
            if not user or not user.is_authenticated:
                return False
            if not user.is_active or user.is_deleted:
                return False
            role = getattr(user, "role", None)
            if role is None:
                return False
            return role.permissions.filter(code=code).exists()

    return _Required
