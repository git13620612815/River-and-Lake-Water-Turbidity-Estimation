from django.urls import path

from apps.detection.views import dashboard
from apps.rbac.views import permission_list, role_detail, roles

urlpatterns = [
    path("dashboard/", dashboard),
    path("permissions/", permission_list),
    path("roles/", roles),
    path("roles/<int:role_id>/", role_detail),
]
