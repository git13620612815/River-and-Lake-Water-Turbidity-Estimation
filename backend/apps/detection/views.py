from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser

from apps.common import paginate
from apps.detection.models import DetectionBatch, DetectionRecord
from apps.detection.services import (
    add_image,
    batch_payload,
    create_batch,
    delete_records,
    record_payload,
    start_batch,
)
from apps.users.services import can_enter_admin, permission_codes
from config.permissions import permission_required
from config.responses import fail, ok


def _owns_or_admin(user, owner_id):
    return owner_id == user.id or can_enter_admin(user)


@api_view(["POST"])
@permission_classes([permission_required("detect.create")])
def create_detection_batch(request):
    try:
        batch = create_batch(request.user, request.data.get("total"))
    except ValueError as exc:
        return fail(str(exc))
    return ok(batch_payload(batch))


@api_view(["GET"])
@permission_classes([permission_required("record.view")])
def batch_detail(request, batch_id):
    batch = DetectionBatch.objects.filter(id=batch_id).first()
    if batch is None or not _owns_or_admin(request.user, batch.user_id):
        return fail("批次不存在", 404)
    return ok(batch_payload(batch))


@api_view(["POST"])
@permission_classes([permission_required("detect.create")])
@parser_classes([MultiPartParser])
def upload_batch_image(request, batch_id):
    batch = DetectionBatch.objects.filter(id=batch_id, user=request.user).first()
    if batch is None:
        return fail("批次不存在", 404)
    try:
        record = add_image(batch, request.FILES.get("file"))
    except ValueError as exc:
        return fail(str(exc))
    return ok(record_payload(record))


@api_view(["POST"])
@permission_classes([permission_required("detect.create")])
def start_detection_batch(request, batch_id):
    batch = DetectionBatch.objects.filter(id=batch_id, user=request.user).first()
    if batch is None:
        return fail("批次不存在", 404)
    try:
        batch = start_batch(batch)
    except ValueError as exc:
        return fail(str(exc))
    return ok(batch_payload(batch))


@api_view(["GET"])
@permission_classes([permission_required("record.view")])
def record_list(request):
    requested = (request.GET.get("user_id") or "").strip()
    if can_enter_admin(request.user):
        queryset = DetectionRecord.objects.select_related("user").all()
        if requested:
            queryset = queryset.filter(user_id=requested)
    else:
        if requested:
            return fail("没有权限", 403)
        queryset = DetectionRecord.objects.select_related("user").filter(user=request.user)
    queryset = queryset.order_by("-created_at", "-id")
    label = (request.GET.get("label") or "").strip()
    if label:
        queryset = queryset.filter(label=label)
    start = (request.GET.get("start") or "").strip()
    end = (request.GET.get("end") or "").strip()
    if start:
        queryset = queryset.filter(created_at__date__gte=start)
    if end:
        queryset = queryset.filter(created_at__date__lte=end)
    return ok(paginate(request, queryset, record_payload))


@api_view(["GET", "DELETE"])
@permission_classes([permission_required("record.view")])
def record_detail(request, record_id):
    record = DetectionRecord.objects.filter(id=record_id).first()
    if record is None or not _owns_or_admin(request.user, record.user_id):
        return fail("记录不存在", 404)
    if request.method == "GET":
        return ok(record_payload(record))
    if "record.delete" not in permission_codes(request.user):
        return fail("没有权限", 403)
    if record.user_id != request.user.id:
        return fail("只能删除自己的记录", 403)
    delete_records(request.user, [record.id])
    return ok(None)


@api_view(["POST"])
@permission_classes([permission_required("record.delete")])
def bulk_delete_records(request):
    ids = request.data.get("ids")
    if not isinstance(ids, list) or not ids:
        return fail("请选择要删除的记录")
    try:
        delete_records(request.user, ids)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except (TypeError, ValueError):
        return fail("记录编号无效")
    return ok(None)


@api_view(["GET"])
@permission_classes([permission_required("dashboard.view")])
def dashboard(request):
    from apps.datasets.models import DatasetImage
    from apps.users.models import User
    from ml.estimator import LABELS
    from ml.infer import weights_ready

    today = timezone.localdate()
    start = today - timedelta(days=6)
    level_counts = {
        label: DetectionRecord.objects.filter(status="success", label=label).count() for label in LABELS
    }
    daily_counts = []
    for offset in range(7):
        day = start + timedelta(days=offset)
        daily_counts.append(
            {"date": day.isoformat(), "count": DetectionRecord.objects.filter(created_at__date=day).count()}
        )
    dataset_counts = {label: DatasetImage.objects.filter(label=label).count() for label in LABELS}
    return ok(
        {
            "user_count": User.objects.filter(is_deleted=False).count(),
            "today_detection_count": DetectionRecord.objects.filter(created_at__date=today).count(),
            "dataset_count": DatasetImage.objects.count(),
            "model_ready": weights_ready(),
            "level_counts": level_counts,
            "daily_counts": daily_counts,
            "dataset_counts": dataset_counts,
            "min_recommended": 50,
        }
    )
