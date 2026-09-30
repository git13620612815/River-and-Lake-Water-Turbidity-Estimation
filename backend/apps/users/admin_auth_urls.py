from django.urls import path

from apps.users.views import admin_login, change_own_password

urlpatterns = [
    path("login/", admin_login),
    path("password/", change_own_password),
]
