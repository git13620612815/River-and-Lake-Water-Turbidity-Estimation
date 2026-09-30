from django.urls import path

from apps.users.views import admin_user_detail, admin_users

urlpatterns = [
    path("", admin_users),
    path("<int:user_id>/", admin_user_detail),
]
