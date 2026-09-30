from django.conf import settings
from django.core.management.base import BaseCommand

from apps.rbac.models import Permission, Role
from apps.users.models import User

PERMISSIONS = [
    ("查看个人资料", "profile.view", "auth"),
    ("修改个人资料", "profile.edit", "auth"),
    ("上传并检测", "detect.create", "detect"),
    ("查看历史记录", "record.view", "detect"),
    ("删除历史记录", "record.delete", "detect"),
    ("用户管理", "user.manage", "admin"),
    ("角色权限管理", "role.manage", "admin"),
    ("数据集管理", "dataset.manage", "admin"),
    ("查看后台概览", "dashboard.view", "admin"),
]

USER_CODES = [
    "profile.view",
    "profile.edit",
    "detect.create",
    "record.view",
    "record.delete",
]


class Command(BaseCommand):
    help = "初始化角色、权限和默认管理员"

    def handle(self, *args, **options):
        for name, code, module in PERMISSIONS:
            Permission.objects.update_or_create(code=code, defaults={"name": name, "module": module})
        admin_role, _ = Role.objects.get_or_create(
            code="admin", defaults={"name": "管理员", "is_builtin": True, "description": "系统管理员"}
        )
        user_role, _ = Role.objects.get_or_create(
            code="user", defaults={"name": "普通用户", "is_builtin": True, "description": "普通用户"}
        )
        admin_role.name = "管理员"
        admin_role.is_builtin = True
        admin_role.save(update_fields=["name", "is_builtin"])
        user_role.name = "普通用户"
        user_role.is_builtin = True
        user_role.save(update_fields=["name", "is_builtin"])
        admin_role.permissions.set(Permission.objects.all())
        user_role.permissions.set(Permission.objects.filter(code__in=USER_CODES))
        username = settings.ADMIN_USERNAME
        admin = User.objects.filter(username=username).first()
        legacy = User.objects.filter(openid=settings.ADMIN_OPENID).first()
        if admin is None and legacy is not None and legacy.username in (None, ""):
            legacy.username = username
            legacy.openid = None
            legacy.role = admin_role
            legacy.is_active = True
            legacy.is_deleted = False
            legacy.nickname = legacy.nickname or "管理员"
            if not legacy.has_usable_password():
                legacy.set_password(settings.ADMIN_PASSWORD)
            legacy.save()
            admin = legacy
        elif admin is None:
            admin = User.objects.create_user(
                username=username,
                password=settings.ADMIN_PASSWORD,
                nickname="管理员",
                role=admin_role,
                is_active=True,
            )
        else:
            admin.role = admin_role
            admin.is_active = True
            admin.is_deleted = False
            admin.save(update_fields=["role", "is_active", "is_deleted"])
        self.stdout.write(self.style.SUCCESS(f"初始化完成，管理员用户名={username}"))
