from django.db import models


class Permission(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    module = models.CharField(max_length=32)

    class Meta:
        db_table = "permissions"

    def __str__(self):
        return self.code


class Role(models.Model):
    name = models.CharField(max_length=32)
    code = models.CharField(max_length=32, unique=True)
    is_builtin = models.BooleanField(default=False)
    description = models.CharField(max_length=200, blank=True, default="")
    permissions = models.ManyToManyField(Permission, through="RolePermission", related_name="roles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "role_permissions"
        unique_together = ("role", "permission")
