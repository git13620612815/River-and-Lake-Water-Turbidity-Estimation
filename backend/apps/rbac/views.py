import re

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission

from apps.rbac.models import Permission, Role
from config.permissions import permission_required
from config.responses import fail, ok

CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
ADMIN_LOCKED = ("user.manage", "role.manage")


def role_payload(role):
    permissions = list(role.permissions.values("id", "name", "code", "module"))
    return {
        "id": role.id,
        "name": role.name,
        "code": role.code,
        "is_builtin": role.is_builtin,
        "description": role.description,
        "permission_ids": [item["id"] for item in permissions],
        "permissions": permissions,
    }


def _permission_ids(raw_ids, role):
    try:
        ids = [int(item) for item in raw_ids]
    except (TypeError, ValueError):
        raise ValueError("权限编号无效")
    found = list(Permission.objects.filter(id__in=ids))
    if len(found) != len(set(ids)):
        raise ValueError("存在无效权限")
    if role is not None and role.code == "admin":
        locked = Permission.objects.filter(code__in=ADMIN_LOCKED)
        merged = {item.id for item in found} | set(locked.values_list("id", flat=True))
        return list(merged)
    return [item.id for item in found]


@api_view(["GET"])
@permission_classes([permission_required("role.manage")])
def permission_list(request):
    rows = list(Permission.objects.order_by("id").values("id", "name", "code", "module"))
    return ok(rows)


class CanReadRoles(BasePermission):
    message = "没有权限"

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not getattr(user, "role_id", None):
            return False
        codes = ["role.manage"]
        if request.method == "GET":
            codes.append("user.manage")
        return user.role.permissions.filter(code__in=codes).exists()


@api_view(["GET", "POST"])
@permission_classes([CanReadRoles])
def roles(request):
    if request.method == "GET":
        return ok([role_payload(role) for role in Role.objects.order_by("id")])
    name = str(request.data.get("name") or "").strip()
    code = str(request.data.get("code") or "").strip()
    if not name:
        return fail("角色名称不能为空")
    if not CODE_RE.match(code):
        return fail("角色编码需为小写字母、数字或下划线")
    if Role.objects.filter(code=code).exists():
        return fail("角色编码已存在")
    role = Role.objects.create(
        name=name[:32],
        code=code,
        description=str(request.data.get("description") or "")[:200],
        is_builtin=False,
    )
    try:
        role.permissions.set(_permission_ids(request.data.get("permission_ids") or [], role))
    except ValueError as exc:
        role.delete()
        return fail(str(exc))
    return ok(role_payload(role))


@api_view(["PATCH", "DELETE"])
@permission_classes([permission_required("role.manage")])
def role_detail(request, role_id):
    role = Role.objects.filter(id=role_id).first()
    if role is None:
        return fail("角色不存在", 404)
    if request.method == "DELETE":
        if role.is_builtin:
            return fail("内置角色不可删除")
        if role.users.exists():
            return fail("仍有用户使用该角色")
        role.delete()
        return ok(None)
    name = str(request.data.get("name") or role.name).strip()
    if not name:
        return fail("角色名称不能为空")
    role.name = name[:32]
    if "description" in request.data:
        role.description = str(request.data.get("description") or "")[:200]
    if "permission_ids" in request.data:
        try:
            role.permissions.set(_permission_ids(request.data.get("permission_ids") or [], role))
        except ValueError as exc:
            return fail(str(exc))
    role.save()
    return ok(role_payload(role))
