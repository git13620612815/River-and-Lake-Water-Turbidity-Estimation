import uuid
from pathlib import Path

from django.utils import timezone as dj_timezone

from django.conf import settings
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def media_url(relative):
    relative = relative.replace("\\", "/")
    if relative.startswith("/media/"):
        return relative
    return "/media/" + relative.lstrip("/")


def media_abspath(stored):
    relative = stored
    if relative.startswith("/media/"):
        relative = relative[len("/media/") :]
    return Path(settings.MEDIA_ROOT) / relative


def delete_media(stored):
    if not stored:
        return
    path = media_abspath(stored)
    if path.is_file():
        path.unlink()


def _ext(uploaded):
    name = (uploaded.name or "").lower()
    return Path(name).suffix


def inspect_image(uploaded):
    ext = _ext(uploaded)
    if ext not in ALLOWED_EXT:
        return None, "仅支持 jpg、jpeg、png、webp"
    if uploaded.size > settings.MAX_UPLOAD_BYTES:
        return None, "文件超过 10MB"
    try:
        uploaded.seek(0)
        image = Image.open(uploaded)
        image.verify()
        uploaded.seek(0)
        image = Image.open(uploaded)
        image.load()
        width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError):
        return None, "解码失败"
    finally:
        uploaded.seek(0)
    return (width, height), ""


def save_upload(uploaded, folder):
    ext = _ext(uploaded)
    relative = f"{folder}/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}"
    path = Path(settings.MEDIA_ROOT) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        for chunk in uploaded.chunks():
            handle.write(chunk)
    return media_url(relative)


def fmt_dt(value):
    if not value:
        return ""
    return dj_timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")


def paginate(request, queryset, dump):
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
    except (TypeError, ValueError):
        page, page_size = 1, 10
    page = max(page, 1)
    page_size = min(max(page_size, 1), 50)
    total = queryset.count()
    start = (page - 1) * page_size
    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": [dump(obj) for obj in queryset[start : start + page_size]],
    }
