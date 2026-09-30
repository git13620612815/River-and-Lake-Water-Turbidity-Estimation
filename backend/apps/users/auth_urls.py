from django.urls import path

from apps.users.views import app_login, app_register, auth_config, refresh_token, wechat_login

urlpatterns = [
    path("config/", auth_config),
    path("login/", app_login),
    path("register/", app_register),
    path("wechat/", wechat_login),
    path("refresh/", refresh_token),
]
