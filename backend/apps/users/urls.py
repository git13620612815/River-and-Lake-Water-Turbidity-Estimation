from django.urls import path

from apps.users.views import me, upload_avatar

urlpatterns = [
    path("me/", me),
    path("me/avatar/", upload_avatar),
]
