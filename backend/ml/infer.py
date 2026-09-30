"""浊度推理。有 YOLOv8 权重时走分类模型，否则用图像特征模型。"""

import threading
from pathlib import Path

from django.conf import settings

from ml.estimator import LABELS, estimate

_lock = threading.Lock()
_cache = None
_ALIASES = {
    "clear": "clear",
    "slight": "slight",
    "moderate": "moderate",
    "severe": "severe",
    "清澈": "clear",
    "轻度浑浊": "slight",
    "中度浑浊": "moderate",
    "重度浑浊": "severe",
}


class ModelNotReady(Exception):
    def __init__(self, message="模型权重未就绪"):
        super().__init__(message)


def weights_ready():
    return Path(settings.MODEL_WEIGHTS).is_file()


def get_model():
    global _cache
    if _cache is not None:
        return _cache
    if not weights_ready():
        raise ModelNotReady("模型权重未就绪")
    try:
        import torch
        from ultralytics import YOLO
    except ImportError as exc:
        raise ModelNotReady("模型依赖未安装或权重未就绪") from exc
    yolo = YOLO(str(settings.MODEL_WEIGHTS))
    net = yolo.model
    net.eval()
    names = yolo.names or {}
    _cache = {"net": net, "torch": torch, "names": names}
    return _cache


def _class_name(names, index):
    raw = names[index] if isinstance(names, dict) else names[index]
    return _ALIASES.get(str(raw).strip())


def _named_probs(cache, tensor):
    torch = cache["torch"]
    with torch.no_grad():
        logits = cache["net"](tensor)
        if isinstance(logits, (list, tuple)):
            logits = logits[0]
        if hasattr(logits, "logits"):
            logits = logits.logits
        probs = torch.softmax(logits, dim=1)[0].detach().cpu().tolist()
    names = cache["names"]
    if names:
        count = len(names)
        mapped = [_class_name(names, index) for index in range(count)]
        if sorted(item for item in mapped if item) != sorted(LABELS):
            raise ModelNotReady("模型类别数不是 4，不能映射为浊度等级")
        named = {label: 0.0 for label in LABELS}
        for index, value in enumerate(probs):
            label = mapped[index]
            if label:
                named[label] = float(value)
        return named
    if len(probs) != len(LABELS):
        raise ModelNotReady("模型类别数不是 4，不能映射为浊度等级")
    return {label: float(probs[index]) for index, label in enumerate(LABELS)}


def _predict_yolo(image_path):
    from ml.preprocess import preprocess_for_infer

    with _lock:
        cache = get_model()
        image = preprocess_for_infer(image_path)
        torch = cache["torch"]
        try:
            device = next(cache["net"].parameters()).device
        except StopIteration:
            device = torch.device("cpu")
        tensor = torch.tensor(image, device=device).unsqueeze(0).float()
        named = _named_probs(cache, tensor)
    return estimate(named)


def predict(image_path):
    if weights_ready():
        return _predict_yolo(image_path)
    from ml.visual import predict_visual

    return predict_visual(image_path)


def reset_model_cache():
    global _cache
    with _lock:
        _cache = None
