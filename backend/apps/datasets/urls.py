from django.urls import path

from apps.datasets.views import dataset_detail, dataset_list, dataset_replace, dataset_stats

urlpatterns = [
    path("stats/", dataset_stats),
    path("", dataset_list),
    path("<int:image_id>/replace/", dataset_replace),
    path("<int:image_id>/", dataset_detail),
]
