import json
import logging
import threading
from datetime import timedelta

from django.db import connection
from django.utils import timezone

from apps.common import delete_media, fmt_dt, inspect_image, media_abspath, save_upload
from apps.detection.models import DetectionBatch, DetectionRecord
from ml.estimator import DESCRIPTIONS, LABEL_NAMES
from ml.infer import ModelNotReady, predict

logger = logging.getLogger(__name__)
DONE = ("success", "failed")
WORKING = ("pending", "preprocessing", "inferring")


def record_payload(record):
    probabilities = None
    if record.probabilities:
        probabilities = json.loads(record.probabilities)
    return {
        "id": record.id,
        "batch_id": record.batch_id,
        "status": record.status,
        "image": record.image,
        "label": record.label,
        "label_name": LABEL_NAMES.get(record.label, ""),
        "confidence": record.confidence,
        "probabilities": probabilities,
        "ntu": record.ntu,
        "ntu_min": record.ntu_min,
        "ntu_max": record.ntu_max,
        "low_confidence": record.low_confidence,
        "description": DESCRIPTIONS.get(record.label, ""),
        "note": record.note,
        "error_message": record.error_message,
        "created_at": fmt_dt(record.created_at),
        "user": {
            "id": record.user_id,
            "nickname": record.user.nickname if record.user_id else "",
        },
    }


def batch_payload(batch):
    records = batch.records.all().order_by("id")
    return {
        "id": batch.id,
        "status": batch.status,
        "total": batch.total,
        "uploaded": batch.uploaded,
        "finished": batch.finished,
        "records": [record_payload(item) for item in records],
    }


def create_batch(user, total):
    try:
        total = int(total)
    except (TypeError, ValueError):
        raise ValueError("请指定图片数量")
    if total < 1 or total > 9:
        raise ValueError("一次最多上传 9 张")
    return DetectionBatch.objects.create(user=user, total=total)


def add_image(batch, uploaded):
    if batch.status != "collecting":
        raise ValueError("批次已开始，不能继续上传")
    if batch.uploaded >= batch.total:
        raise ValueError("上传数量已达到批次上限")
    record = DetectionRecord(batch=batch, user_id=batch.user_id)
    if uploaded is None:
        record.status = "failed"
        record.error_message = "请选择图片"
    else:
        meta, error = inspect_image(uploaded)
        if error:
            record.status = "failed"
            record.error_message = error
        else:
            record.image = save_upload(uploaded, "uploads")
            record.status = "pending"
    record.save()
    batch.uploaded += 1
    if record.status == "failed":
        batch.finished += 1
    batch.save(update_fields=["uploaded", "finished", "updated_at"])
    return record


def _apply_result(record, result):
    record.label = result["label"]
    record.confidence = result["confidence"]
    record.probabilities = json.dumps(result["probabilities"], ensure_ascii=False)
    record.ntu = result["ntu"]
    record.ntu_min = result["ntu_min"]
    record.ntu_max = result["ntu_max"]
    record.low_confidence = result["low_confidence"]
    record.note = result["note"]
    record.status = "success"
    record.error_message = ""


def _refresh_batch(batch_id):
    batch = DetectionBatch.objects.get(pk=batch_id)
    batch.finished = batch.records.filter(status__in=DONE).count()
    if batch.status != "collecting" and not batch.records.filter(status__in=WORKING).exists():
        batch.status = "finished"
    batch.save(update_fields=["finished", "status", "updated_at"])


def run_record(record_id):
    record = DetectionRecord.objects.get(pk=record_id)
    if record.status != "pending":
        _refresh_batch(record.batch_id)
        return
    try:
        record.status = "preprocessing"
        record.save(update_fields=["status"])
        record.status = "inferring"
        record.save(update_fields=["status"])
        result = predict(str(media_abspath(record.image)))
        _apply_result(record, result)
    except ModelNotReady as exc:
        record.status = "failed"
        record.error_message = str(exc)[:255]
    except Exception:
        logger.exception("推理失败 record=%s", record_id)
        record.status = "failed"
        record.error_message = "推理失败"
    record.save()
    _refresh_batch(record.batch_id)


def _run_many(record_ids):
    try:
        for record_id in record_ids:
            run_record(record_id)
    finally:
        connection.close()


def start_batch(batch):
    if batch.status != "collecting":
        raise ValueError("批次已开始")
    if batch.uploaded != batch.total:
        raise ValueError("图片尚未上传齐全")
    pending_ids = list(batch.records.filter(status="pending").values_list("id", flat=True))
    if not pending_ids:
        batch.finished = batch.records.filter(status__in=DONE).count()
        batch.status = "finished"
        batch.save(update_fields=["finished", "status", "updated_at"])
        return batch
    batch.status = "running"
    batch.save(update_fields=["status", "updated_at"])
    if batch.total == 1:
        run_record(pending_ids[0])
    else:
        threading.Thread(target=_run_many, args=(pending_ids,), daemon=True).start()
    batch.refresh_from_db()
    return batch


def delete_records(user, ids):
    unique_ids = list({int(item) for item in ids})
    queryset = DetectionRecord.objects.filter(id__in=unique_ids, user=user)
    if queryset.count() != len(unique_ids):
        raise PermissionError("只能删除自己的记录")
    images = list(queryset.values_list("image", flat=True))
    batch_ids = list(queryset.values_list("batch_id", flat=True))
    queryset.delete()
    for image in images:
        delete_media(image)
    DetectionBatch.objects.filter(id__in=batch_ids, records__isnull=True).delete()


def fail_stale_batches():
    deadline = timezone.now() - timedelta(minutes=10)
    batches = DetectionBatch.objects.filter(status="running", updated_at__lt=deadline)
    for batch in batches:
        batch.records.filter(status__in=WORKING).update(status="failed", error_message="处理超时，请重试")
        batch.finished = batch.records.filter(status__in=DONE).count()
        batch.status = "finished"
        batch.save(update_fields=["finished", "status", "updated_at"])
