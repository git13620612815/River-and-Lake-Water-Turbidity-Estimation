from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, password=None, **extra):
        openid = (extra.pop("openid", None) or "").strip() or None
        username = (extra.pop("username", None) or "").strip() or None
        if not openid and not username:
            raise ValueError("openid 和 username 至少填一个")
        user = self.model(openid=openid, username=username, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    openid = models.CharField(max_length=64, unique=True, null=True, blank=True)
    username = models.CharField(max_length=64, unique=True, null=True, blank=True)
    nickname = models.CharField(max_length=64, default="微信用户")
    avatar = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    role = models.ForeignKey("rbac.Role", null=True, on_delete=models.PROTECT, related_name="users")
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = "users"

    def save(self, *args, **kwargs):
        self.openid = (self.openid or "").strip() or None
        self.username = (self.username or "").strip() or None
        if not self.openid and not self.username:
            raise ValueError("openid 和 username 至少填一个")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nickname or self.username or self.openid or str(self.pk)
