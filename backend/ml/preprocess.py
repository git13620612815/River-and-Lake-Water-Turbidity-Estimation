"""推理前预处理：等比缩放、居中裁剪到 224，像素缩放到 0～1。

当前 ultralytics 分类训练使用 mean=0、std=1，不再额外做 ImageNet 归一化。
线上推理必须和这一步一致，否则同一张图会判错等级。
"""

from PIL import Image

SIZE = 224


def center_crop_resize(image, size=SIZE):
    image = image.convert("RGB")
    width, height = image.size
    scale = size / min(width, height)
    resized = image.resize((max(size, round(width * scale)), max(size, round(height * scale))), Image.BILINEAR)
    rw, rh = resized.size
    left = max(0, (rw - size) // 2)
    top = max(0, (rh - size) // 2)
    return resized.crop((left, top, left + size, top + size))


def preprocess_for_infer(image_path):
    from ultralytics.data.augment import classify_transforms

    image = Image.open(image_path).convert("RGB")
    return classify_transforms(SIZE)(image).numpy()
