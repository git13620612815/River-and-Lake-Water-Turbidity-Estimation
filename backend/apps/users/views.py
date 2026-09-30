from django.conf import settings
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from apps.common import delete_media, inspect_image, paginate, save_upload
from apps.rbac.models import Role
from apps.users.models import User
from apps.users.services import (
    can_enter_admin,
    change_password,
    clean_nickname,
    clean_phone,
    is_last_active_admin,
    issue_token,
    login_app_by_password,
    login_by_code,
    login_by_password,
    register_user,
    user_payload,
)
from config.permissions import permission_required
from config.responses import fail, ok
from ml.infer import weights_ready


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return ok({"status": "ok", "model_ready": weights_ready()})


@api_view(["GET"])
@permission_classes([AllowAny])
def auth_config(request):
    return ok({"mock": settings.WECHAT_MOCK, "wechat": bool(settings.WECHAT_APPID and settings.WECHAT_SECRET)})


@api_view(["POST"])
@permission_classes([AllowAny])
def wechat_login(request):
    try:
        data = login_by_code(request.data.get("code"))
    except PermissionError as exc:
        return fail(str(exc), 403)
    except ValueError as exc:
        return fail(str(exc))
    except Exception:
        return fail("微信登录失败")
    return ok(data)


@api_view(["POST"])
@permission_classes([AllowAny])
def app_login(request):
    try:
        data = login_app_by_password(request.data.get("username"), request.data.get("password"))
    except PermissionError as exc:
        return fail(str(exc), 403)
    except ValueError as exc:
        return fail(str(exc))
    return ok(data)


@api_view(["POST"])
@permission_classes([AllowAny])
def app_register(request):
    try:
        data = register_user(
            request.data.get("username"),
            request.data.get("password"),
            request.data.get("nickname") or "",
        )
    except ValueError as exc:
        return fail(str(exc))
    return ok(data)


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    serializer = TokenRefreshSerializer(data=request.data)
    try:
        serializer.is_valid(raise_exception=True)
    except TokenError:
        return fail("登录已过期", 401)
    except Exception as exc:
        from rest_framework.exceptions import APIException

        if isinstance(exc, APIException):
            return fail("登录已过期", 401)
        raise
    return ok(serializer.validated_data)


@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    try:
        data = login_by_password(request.data.get("username"), request.data.get("password"))
    except PermissionError as exc:
        return fail(str(exc), 403)
    except ValueError as exc:
        return fail(str(exc))
    return ok(data)


@api_view(["POST"])
def change_own_password(request):
    if not can_enter_admin(request.user):
        return fail("无权进入管理端", 403)
    try:
        change_password(request.user, request.data.get("old_password"), request.data.get("new_password"))
    except ValueError as exc:
        return fail(str(exc))
    return ok(None)


@api_view(["GET", "PATCH"])
@permission_classes([permission_required("profile.view")])
def me(request):
    user = request.user
    if request.method == "GET":
        return ok(user_payload(user))
    if not user.role.permissions.filter(code="profile.edit").exists():
        return fail("没有权限", 403)
    try:
        if "nickname" in request.data:
            user.nickname = clean_nickname(request.data.get("nickname"))
        if "phone" in request.data:
            user.phone = clean_phone(request.data.get("phone"))
    except ValueError as exc:
        return fail(str(exc))
    user.save(update_fields=["nickname", "phone", "updated_at"])
    return ok(user_payload(user))


@api_view(["POST"])
@permission_classes([permission_required("profile.edit")])
@parser_classes([MultiPartParser])
def upload_avatar(request):
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return fail("请选择头像")
    meta, error = inspect_image(uploaded)
    if error:
        return fail(error)
    url = save_upload(uploaded, "avatars")
    delete_media(request.user.avatar)
    request.user.avatar = url
    request.user.save(update_fields=["avatar", "updated_at"])
    return ok(user_payload(request.user))


def _role_from_body(data, default_code="user"):
    if data.get("role_id"):
        role = Role.objects.filter(id=data.get("role_id")).first()
    elif data.get("role"):
        role = Role.objects.filter(code=data.get("role")).first()
    else:
        role = Role.objects.filter(code=default_code).first()
    return role


@api_view(["GET", "POST"])
@permission_classes([permission_required("user.manage")])
def admin_users(request):
    if request.method == "GET":
        queryset = User.objects.filter(is_deleted=False).select_related("role").order_by("-id")
        nickname = (request.GET.get("nickname") or "").strip()
        if nickname:
            queryset = queryset.filter(nickname__icontains=nickname)
        role = (request.GET.get("role") or "").strip()
        if role:
            queryset = queryset.filter(role__code=role)
        active = request.GET.get("is_active")
        if active in ("0", "1", "true", "false"):
            queryset = queryset.filter(is_active=active in ("1", "true"))
        return ok(paginate(request, queryset, lambda item: user_payload(item, admin=True)))

    openid = str(request.data.get("openid") or "").strip() or None
    username = str(request.data.get("username") or "").strip() or None
    password = str(request.data.get("password") or "")
    if not openid and not username:
        return fail("请填写 openid 或用户名")
    if username and not password:
        return fail("设置用户名时必须填写密码")
    if password and not username:
        return fail("设置密码时必须填写用户名")
    if openid and User.objects.filter(openid=openid).exists():
        return fail("openid 已存在")
    if username and User.objects.filter(username=username).exists():
        return fail("用户名已存在")
    role = _role_from_body(request.data)
    if role is None:
        return fail("角色不存在")
    try:
        nickname = clean_nickname(request.data.get("nickname") or "微信用户")
        phone = clean_phone(request.data.get("phone"))
    except ValueError as exc:
        return fail(str(exc))
    user = User.objects.create_user(
        openid=openid, username=username, password=password or None, nickname=nickname, phone=phone, role=role
    )
    return ok(user_payload(user, admin=True))


@api_view(["PATCH", "DELETE"])
@permission_classes([permission_required("user.manage")])
def admin_user_detail(request, user_id):
    user = User.objects.filter(id=user_id, is_deleted=False).select_related("role").first()
    if user is None:
        return fail("用户不存在", 404)
    if request.method == "DELETE":
        if user.id == request.user.id:
            return fail("不能删除当前登录账号")
        if is_last_active_admin(user):
            return fail("不能删除系统中最后一个管理员")
        from apps.detection.models import DetectionRecord

        delete_media(user.avatar)
        for image in DetectionRecord.objects.filter(user=user).values_list("image", flat=True):
            delete_media(image)
        user.delete()
        return ok(None)
    if "nickname" in request.data:
        try:
            user.nickname = clean_nickname(request.data.get("nickname"))
        except ValueError as exc:
            return fail(str(exc))
    if "phone" in request.data:
        try:
            user.phone = clean_phone(request.data.get("phone"))
        except ValueError as exc:
            return fail(str(exc))
    if "username" in request.data:
        username = str(request.data.get("username") or "").strip() or None
        if username and User.objects.exclude(id=user.id).filter(username=username).exists():
            return fail("用户名已存在")
        user.username = username
    if request.data.get("password"):
        if not (user.username or str(request.data.get("username") or "").strip()):
            return fail("设置密码时必须填写用户名")
        if len(str(request.data.get("password"))) < 6:
            return fail("密码至少 6 位")
        user.set_password(str(request.data.get("password")))
    if "openid" in request.data:
        openid = str(request.data.get("openid") or "").strip() or None
        if openid and User.objects.exclude(id=user.id).filter(openid=openid).exists():
            return fail("openid 已存在")
        user.openid = openid
    if not (user.openid or user.username):
        return fail("openid 和用户名至少保留一个")
    if "role_id" in request.data or "role" in request.data:
        role = _role_from_body(request.data, default_code="")
        if role is None:
            return fail("角色不存在")
        if user.role_id and user.role.code == "admin" and role.code != "admin" and is_last_active_admin(user):
            return fail("不能取消最后一个管理员")
        user.role = role
    if "is_active" in request.data:
        raw_active = request.data.get("is_active")
        active = raw_active if isinstance(raw_active, bool) else str(raw_active).lower() in ("1", "true", "yes")
        if user.id == request.user.id and not active:
            return fail("不能停用当前登录账号")
        if not active and is_last_active_admin(user):
            return fail("不能停用最后一个管理员")
        user.is_active = active
    user.save()
    return ok(user_payload(user, admin=True))
