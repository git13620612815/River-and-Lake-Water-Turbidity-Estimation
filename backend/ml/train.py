"""离线训练。在 backend 目录执行：

python ml/train.py --data ml/data --epochs 50 --imgsz 224 --model yolov8n-cls.pt
"""

import argparse
import random
import shutil
from pathlib import Path

LABELS = ("clear", "slight", "moderate", "severe")


def split_dataset(source: Path, target: Path):
    if target.exists():
        shutil.rmtree(target)
    buckets = ("train", "val", "test")
    ratios = (0.7, 0.15, 0.15)
    for label in LABELS:
        files = [
            path
            for path in (source / label).glob("*")
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
        random.Random(42).shuffle(files)
        n = len(files)
        if n < 20:
            n_val = 1
            n_test = 1
        else:
            n_val = max(1, int(round(n * ratios[1])))
            n_test = max(1, int(round(n * ratios[2])))
        if n_val + n_test >= n:
            n_val = 1
            n_test = 1
        n_train = n - n_val - n_test
        groups = {
            "train": files[:n_train],
            "val": files[n_train : n_train + n_val],
            "test": files[n_train + n_val :],
        }
        for bucket in buckets:
            folder = target / bucket / label
            folder.mkdir(parents=True, exist_ok=True)
            for path in groups[bucket]:
                shutil.copy2(path, folder / path.name)
        print(f"{label}: {n} 张")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="ml/data")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=224)
    parser.add_argument("--model", default="yolov8n-cls.pt")
    args = parser.parse_args()
    source = Path(args.data)
    suffixes = {".jpg", ".jpeg", ".png", ".webp"}
    for label in LABELS:
        folder = source / label
        count = 0
        if folder.is_dir():
            count = sum(1 for path in folder.iterdir() if path.suffix.lower() in suffixes)
        if count < 4:
            raise SystemExit(f"{label} 只有 {count} 张，至少 4 张才能训练。请先在管理端补图。")
    staged = source.parent / "data_split"
    split_dataset(source, staged)
    try:
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit("未安装 ultralytics，无法训练")
    model = YOLO(args.model)
    model.train(
        data=str(staged),
        epochs=args.epochs,
        imgsz=args.imgsz,
        device="cpu",
        workers=0,
        auto_augment=None,
        erasing=0.0,
        hsv_h=0.0,
        name="turbidity",
        exist_ok=True,
        fliplr=0.5,
        degrees=15,
        translate=0.1,
        scale=0.1,
        hsv_v=0.2,
        hsv_s=0.2,
    )
    best = Path(getattr(model.trainer, "best", ""))
    if not best.is_file():
        candidates = sorted(Path("runs").glob("classify/**/weights/best.pt"), key=lambda path: path.stat().st_mtime)
        best = candidates[-1] if candidates else best
    if not best.is_file():
        raise SystemExit("训练结束，但没有找到 best.pt")
    target = Path(__file__).resolve().parent / "weights" / "best.pt"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, target)
    print(f"训练完成，权重已写入 {target}。请重启 Django。")


if __name__ == "__main__":
    main()
