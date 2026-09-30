"""图像特征浊度模型。

没有 YOLOv8 权重时使用。根据水色、饱和度、亮度和画面细节估计浑浊指数，
再转成四类概率，由 estimator 计算等级和 NTU。同一张图结果固定，不是随机数。
"""

import numpy as np
from PIL import Image

from ml.estimator import LABELS, estimate

# 与四个等级在 0~1 浑浊轴上的位置对应
_CENTERS = (0.12, 0.36, 0.60, 0.86)
_SIGMA = 0.16
_NOTE = "当前使用图像特征模型估算。放入 YOLOv8 权重后会自动改用分类模型。"


def _rgb(image_path):
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((512, 512), Image.BICUBIC)
    return np.asarray(image, dtype=np.float32) / 255.0


def _hsv(array):
    red = array[:, :, 0]
    green = array[:, :, 1]
    blue = array[:, :, 2]
    peak = np.maximum(np.maximum(red, green), blue)
    floor = np.minimum(np.minimum(red, green), blue)
    span = peak - floor
    sat = np.divide(span, peak, out=np.zeros_like(span), where=peak > 1e-6)
    hue = np.zeros_like(peak)
    red_max = (peak == red) & (span > 1e-6)
    green_max = (peak == green) & (span > 1e-6) & ~red_max
    blue_max = (peak == blue) & (span > 1e-6) & ~red_max & ~green_max
    hue[red_max] = ((green[red_max] - blue[red_max]) / span[red_max]) % 6
    hue[green_max] = (blue[green_max] - red[green_max]) / span[green_max] + 2
    hue[blue_max] = (red[blue_max] - green[blue_max]) / span[blue_max] + 4
    return hue * 60.0, sat, peak


def turbidity_index(array):
    hue, sat, val = _hsv(array)
    mean_h = float(np.average(hue, weights=np.maximum(sat, 1e-3)))
    mean_s = float(sat.mean())
    mean_v = float(val.mean())
    luma = 0.299 * array[:, :, 0] + 0.587 * array[:, :, 1] + 0.114 * array[:, :, 2]
    if luma.shape[0] > 2 and luma.shape[1] > 2:
        center = luma[1:-1, 1:-1]
        lap = luma[:-2, 1:-1] + luma[2:, 1:-1] + luma[1:-1, :-2] + luma[1:-1, 2:] - 4.0 * center
        sharp = float(np.mean(np.abs(lap)))
    else:
        sharp = 0.0
    detail = float(np.clip(sharp / 0.05, 0.0, 1.0))

    # 发白、低饱和：轻度到中度，不按泥沙色处理
    if mean_s < 0.18:
        index = 0.28 + (mean_v - 0.45) * 0.35 + (1.0 - detail) * 0.06
        return float(np.clip(index, 0.18, 0.55))

    # 偏蓝、偏青：清澈。波纹和底部细节再把指数略往下压。
    if 150 <= mean_h <= 250:
        index = 0.20 - mean_s * 0.10 - detail * 0.06
        return float(np.clip(index, 0.04, 0.34))

    # 黄、褐：越暗、细节越少，越接近重度浑浊
    if 8 <= mean_h <= 75:
        darkness = float(np.clip((0.72 - mean_v) / 0.42, 0.0, 1.0))
        index = 0.52 + darkness * 0.36 + (1.0 - detail) * 0.06
        return float(np.clip(index, 0.45, 0.96))

    index = 0.40 + (1.0 - mean_s) * 0.2
    return float(np.clip(index, 0.2, 0.7))


def probabilities_from_index(index):
    weights = [float(np.exp(-0.5 * ((index - center) / _SIGMA) ** 2)) for center in _CENTERS]
    total = sum(weights) or 1.0
    return {label: weight / total for label, weight in zip(LABELS, weights)}


def predict_visual(image_path):
    index = turbidity_index(_rgb(image_path))
    result = estimate(probabilities_from_index(index))
    result["note"] = f"{result['note']}{_NOTE}" if result["note"] else _NOTE
    return result
