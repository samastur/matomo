"""matomo_django URL Configuration
"""
from django.urls import path
from home.views import HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
]
