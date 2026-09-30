from django.db import models


class DatasetImage(models.Model):
    LABELS = (
        ("clear", "清澈"),
        ("slight", "轻度浑浊"),
        ("moderate", "中度浑浊"),
        ("severe", "重度浑浊"),
    )
    image = models.CharField(max_length=255)
    label = models.CharField(max_length=16, choices=LABELS)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=200, blank=True, default="")
    uploader = models.ForeignKey(
        "users.User", null=True, on_delete=models.SET_NULL, related_name="dataset_images"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dataset_images"
