from django.urls import path

from apps.detection.views import (
    batch_detail,
    bulk_delete_records,
    create_detection_batch,
    record_detail,
    record_list,
    start_detection_batch,
    upload_batch_image,
)

urlpatterns = [
    path("batches/", create_detection_batch),
    path("batches/<int:batch_id>/", batch_detail),
    path("batches/<int:batch_id>/images/", upload_batch_image),
    path("batches/<int:batch_id>/start/", start_detection_batch),
    path("records/", record_list),
    path("records/bulk-delete/", bulk_delete_records),
    path("records/<int:record_id>/", record_detail),
]
