from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.users.views import health

urlpatterns = [
    path("api/health/", health),
    path("api/auth/", include("apps.users.auth_urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/detections/", include("apps.detection.urls")),
    path("api/admin/auth/", include("apps.users.admin_auth_urls")),
    path("api/admin/users/", include("apps.users.admin_urls")),
    path("api/admin/", include("apps.rbac.urls")),
    path("api/admin/datasets/", include("apps.datasets.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
