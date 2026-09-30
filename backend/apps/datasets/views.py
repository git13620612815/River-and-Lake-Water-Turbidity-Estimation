from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser

from apps.common import delete_media, fmt_dt, inspect_image, paginate, save_upload
from apps.datasets.models import DatasetImage
from config.permissions import permission_required
from config.responses import fail, ok
from ml.estimator import LABEL_NAMES, LABELS

MIN_RECOMMENDED = 50


def image_payload(item):
    return {
        "id": item.id,
        "image": item.image,
        "label": item.label,
        "label_name": LABEL_NAMES.get(item.label, ""),
        "width": item.width,
        "height": item.height,
        "note": item.note,
        "uploader_id": item.uploader_id,
        "uploader_name": item.uploader.nickname if item.uploader_id else "",
        "created_at": fmt_dt(item.created_at),
        "updated_at": fmt_dt(item.updated_at),
    }


@api_view(["GET"])
@permission_classes([permission_required("dataset.manage")])
def dataset_stats(request):
    data = {label: DatasetImage.objects.filter(label=label).count() for label in LABELS}
    data["min_recommended"] = MIN_RECOMMENDED
    return ok(data)


@api_view(["GET", "POST"])
@permission_classes([permission_required("dataset.manage")])
@parser_classes([MultiPartParser])
def dataset_list(request):
    if request.method == "GET":
        queryset = DatasetImage.objects.select_related("uploader").order_by("-id")
        label = (request.GET.get("label") or "").strip()
        if label:
            queryset = queryset.filter(label=label)
        return ok(paginate(request, queryset, image_payload))
    uploaded_list = request.FILES.getlist("files")
    if not uploaded_list and request.FILES.get("file"):
        uploaded_list = [request.FILES.get("file")]
    label = str(request.data.get("label") or "").strip()
    if label not in LABELS:
        return fail("请选择浊度等级")
    if not uploaded_list:
        return fail("请选择图片")
    if len(uploaded_list) > 20:
        return fail("一次最多上传 20 张")
    created = []
    errors = []
    note = str(request.data.get("note") or "")[:200]
    for uploaded in uploaded_list:
        meta, error = inspect_image(uploaded)
        if error:
            errors.append({"name": uploaded.name, "message": error})
            continue
        width, height = meta
        item = DatasetImage.objects.create(
            image=save_upload(uploaded, "datasets"),
            label=label,
            width=width,
            height=height,
            note=note,
            uploader=request.user,
        )
        created.append(image_payload(item))
    if not created:
        return fail(errors[0]["message"] if errors else "上传失败")
    if len(uploaded_list) == 1 and not errors:
        return ok(created[0])
    return ok({"created": created, "errors": errors})


@api_view(["PATCH", "DELETE"])
@permission_classes([permission_required("dataset.manage")])
def dataset_detail(request, image_id):
    item = DatasetImage.objects.filter(id=image_id).first()
    if item is None:
        return fail("数据不存在", 404)
    if request.method == "DELETE":
        delete_media(item.image)
        item.delete()
        return ok(None)
    if "label" in request.data:
        label = str(request.data.get("label") or "").strip()
        if label not in LABELS:
            return fail("浊度等级无效")
        item.label = label
    if "note" in request.data:
        item.note = str(request.data.get("note") or "")[:200]
    item.save()
    return ok(image_payload(item))


@api_view(["POST"])
@permission_classes([permission_required("dataset.manage")])
@parser_classes([MultiPartParser])
def dataset_replace(request, image_id):
    item = DatasetImage.objects.filter(id=image_id).select_related("uploader").first()
    if item is None:
        return fail("数据不存在", 404)
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return fail("请选择图片")
    meta, error = inspect_image(uploaded)
    if error:
        return fail(error)
    delete_media(item.image)
    item.image = save_upload(uploaded, "datasets")
    item.width, item.height = meta
    item.save()
    return ok(image_payload(item))
