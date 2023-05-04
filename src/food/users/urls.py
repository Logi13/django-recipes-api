from django.urls import re_path, path, include

from . import views

urlpatterns = [
    re_path(r'login', views.login_view, name='login'),
    re_path(r'profile', views.profile, name='profile')
]