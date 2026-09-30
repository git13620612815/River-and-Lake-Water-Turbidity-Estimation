import re

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common import fmt_dt
from apps.rbac.models import Role
from apps.users.models import User

PHONE_RE = re.compile(r"^1\d{10}$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fff]{3,20}$")


def mask_openid(openid):
    if not openid:
        return ""
    if len(openid) <= 8:
        return openid[:1] + "***"
    return openid[:4] + "****" + openid[-4:]


def permission_codes(user):
    if not user.role_id:
        return []
    return list(user.role.permissions.values_list("code", flat=True))


ADMIN_ENTRY = {"dashboard.view", "user.manage", "role.manage", "dataset.manage"}


def can_enter_admin(user):
    return bool(ADMIN_ENTRY.intersection(permission_codes(user)))


def user_payload(user, admin=False):
    data = {
        "id": user.id,
        "username": user.username or "",
        "nickname": user.nickname,
        "avatar": user.avatar or "",
        "phone": user.phone or "",
        "role": None
        if user.role_id is None
        else {"id": user.role_id, "code": user.role.code, "name": user.role.name},
        "permissions": permission_codes(user),
    }
    if admin:
        data["openid_masked"] = mask_openid(user.openid)
        data["is_active"] = user.is_active
        data["created_at"] = fmt_dt(user.created_at)
    return data


def issue_token(user):
    refresh = RefreshToken.for_user(user)
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": user_payload(user),
    }


def _exchange_openid(code):
    if settings.WECHAT_MOCK:
        text = str(code or "")
        if not text.startswith("mock:") or not text.split(":", 1)[1].strip():
            raise ValueError("开发登录码无效")
        return text.split(":", 1)[1].strip()[:64]
    response = requests.get(
        "https://api.weixin.qq.com/sns/jscode2session",
        params={
            "appid": settings.WECHAT_APPID,
            "secret": settings.WECHAT_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        },
        timeout=5,
    )
    payload = response.json()
    if payload.get("errcode") or not payload.get("openid"):
        raise ValueError("微信登录失败")
    return payload["openid"]


def _authenticate(username, password):
    username = str(username or "").strip()
    user = User.objects.filter(username=username, is_deleted=False).select_related("role").first() if username else None
    if user is None or not user.has_usable_password() or not user.check_password(password or ""):
        raise ValueError("账号或密码错误")
    if not user.is_active:
        raise PermissionError("账号已停用")
    return user


def login_by_password(username, password):
    user = _authenticate(username, password)
    if not can_enter_admin(user):
        raise PermissionError("无权进入管理端")
    return issue_token(user)


def login_app_by_password(username, password):
    return issue_token(_authenticate(username, password))


def clean_username(username):
    username = str(username or "").strip()
    if not USERNAME_RE.match(username):
        raise ValueError("用户名为 3 到 20 位字母、数字或中文")
    return username


def clean_password(password):
    password = str(password or "")
    if len(password) < 6 or len(password) > 32:
        raise ValueError("密码为 6 到 32 位")
    return password


def register_user(username, password, nickname=""):
    username = clean_username(username)
    password = clean_password(password)
    if User.objects.filter(username=username).exists():
        raise ValueError("用户名已存在")
    role = Role.objects.filter(code="user").first()
    if role is None:
        raise ValueError("请先执行 init_rbac 初始化角色")
    nickname = str(nickname or "").strip() or username
    user = User.objects.create_user(
        username=username,
        password=password,
        role=role,
        nickname=clean_nickname(nickname),
    )
    return issue_token(user)


def change_password(user, old_password, new_password):
    if not user.check_password(old_password or ""):
        raise ValueError("原密码错误")
    new_password = str(new_password or "")
    if len(new_password) < 6:
        raise ValueError("新密码至少 6 位")
    user.set_password(new_password)
    user.save(update_fields=["password"])


def login_by_code(code):
    if not code:
        raise ValueError("缺少登录码")
    openid = _exchange_openid(code)
    user = User.objects.filter(openid=openid).first()
    if user and (user.is_deleted or not user.is_active):
        raise PermissionError("账号已停用")
    if user is None:
        role = Role.objects.filter(code="user").first()
        if role is None:
            raise ValueError("请先执行 init_rbac 初始化角色")
        user = User.objects.create_user(openid=openid, role=role, nickname="微信用户")
    return issue_token(user)


def is_last_active_admin(user):
    if not user.role_id or user.role.code != "admin" or not user.is_active:
        return False
    return User.objects.filter(role__code="admin", is_active=True, is_deleted=False).count() <= 1


def clean_phone(phone, allow_empty=True):
    phone = str(phone or "").strip()
    if not phone and allow_empty:
        return ""
    if not PHONE_RE.match(phone):
        raise ValueError("手机号格式错误")
    return phone


def clean_nickname(nickname):
    nickname = str(nickname or "").strip()
    if not nickname:
        raise ValueError("昵称不能为空")
    if len(nickname) > 64:
        raise ValueError("昵称过长")
    return nickname
