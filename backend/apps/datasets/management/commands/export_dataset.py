import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.common import media_abspath
from apps.datasets.models import DatasetImage
from ml.estimator import LABELS


class Command(BaseCommand):
    help = "按类别导出数据集到 ml/data"

    def handle(self, *args, **options):
        root = Path(settings.DATASET_EXPORT_DIR)
        if root.exists():
            shutil.rmtree(root)
        for label in LABELS:
            (root / label).mkdir(parents=True, exist_ok=True)
        count = 0
        for item in DatasetImage.objects.all():
            source = media_abspath(item.image)
            if not source.is_file():
                continue
            shutil.copy2(source, root / item.label / source.name)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"已导出 {count} 张到 {root}"))
