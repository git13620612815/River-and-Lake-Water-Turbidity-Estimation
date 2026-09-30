from django.db import models


class DetectionBatch(models.Model):
    STATUS = (
        ("collecting", "收集中"),
        ("running", "推理中"),
        ("finished", "已完成"),
    )
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="batches")
    total = models.PositiveIntegerField()
    uploaded = models.PositiveIntegerField(default=0)
    finished = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=STATUS, default="collecting")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "detection_batches"


class DetectionRecord(models.Model):
    STATUS = (
        ("pending", "等待"),
        ("preprocessing", "预处理"),
        ("inferring", "推理中"),
        ("success", "成功"),
        ("failed", "失败"),
    )
    batch = models.ForeignKey(DetectionBatch, on_delete=models.CASCADE, related_name="records")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="records")
    image = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS, default="pending")
    error_message = models.CharField(max_length=255, blank=True, default="")
    label = models.CharField(max_length=16, blank=True, default="")
    confidence = models.FloatField(null=True, blank=True)
    probabilities = models.TextField(blank=True, default="")
    ntu = models.FloatField(null=True, blank=True)
    ntu_min = models.FloatField(null=True, blank=True)
    ntu_max = models.FloatField(null=True, blank=True)
    low_confidence = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "detection_records"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "label"]),
        ]
