"""浊度等级与 NTU 估算。分类取最大概率，点估值按代表值加权。"""

LABELS = ("clear", "slight", "moderate", "severe")

LABEL_NAMES = {
    "clear": "清澈",
    "slight": "轻度浑浊",
    "moderate": "中度浑浊",
    "severe": "重度浑浊",
}

CENTERS = {
    "clear": 5,
    "slight": 30,
    "moderate": 125,
    "severe": 400,
}

RANGES = {
    "clear": (0, 10),
    "slight": (10, 50),
    "moderate": (50, 200),
    "severe": (200, 1000),
}

DESCRIPTIONS = {
    "clear": "水体透明，可见较深水下轮廓",
    "slight": "略显发白或淡黄，底部细节下降",
    "moderate": "明显浑浊，透明度差",
    "severe": "严重浑浊，呈泥黄、灰褐或不透明",
}

LOW_CONFIDENCE = 0.45


def estimate(probabilities):
    probs = {}
    for key in LABELS:
        probs[key] = float(probabilities.get(key, 0) or 0)
    total = sum(probs.values())
    if total <= 0:
        raise ValueError("分类概率无效")
    if abs(total - 1) > 1e-3:
        probs = {key: value / total for key, value in probs.items()}

    label = max(LABELS, key=lambda key: probs[key])
    confidence = probs[label]
    ntu = sum(probs[key] * CENTERS[key] for key in LABELS)
    ntu = round(ntu + 1e-9, 1)
    ntu_min, ntu_max = RANGES[label]
    ordered = sorted(LABELS, key=lambda key: probs[key], reverse=True)
    second = ordered[1]
    note = ""
    if ntu < ntu_min or ntu > ntu_max:
        note = (
            f"邻近{LABEL_NAMES[second]}类别占比较高，"
            f"数值偏出{LABEL_NAMES[label]}参考区间，建议结合现场观察。"
        )
    return {
        "label": label,
        "label_name": LABEL_NAMES[label],
        "confidence": confidence,
        "probabilities": {key: probs[key] for key in LABELS},
        "ntu": ntu,
        "ntu_min": ntu_min,
        "ntu_max": ntu_max,
        "low_confidence": confidence < LOW_CONFIDENCE,
        "description": DESCRIPTIONS[label],
        "note": note,
    }
