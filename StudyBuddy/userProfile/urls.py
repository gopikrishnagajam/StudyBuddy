from django.urls import path
from . import views

urlpatterns = [
    path('profile', views.profile, name='profile'),
    path('profile_setup', views.profile_setup, name='profile_setup'),
]
