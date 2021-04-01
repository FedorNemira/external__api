from django.conf.urls import include, url
from django.conf import settings
from django.urls import path
from django.contrib import admin
from bot_interface import views as bot_interface_views


urlpatterns = [
    url(r"^$", bot_interface_views.main),
    url(r'^(?P<user_uuid>[^/]+)/$', bot_interface_views.user_view, name='user_view'),
]


urlpatterns += [
    path("admin/", admin.site.urls),
]

