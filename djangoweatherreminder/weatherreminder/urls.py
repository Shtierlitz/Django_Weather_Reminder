from django.conf.urls import handler404
from django.urls import path
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .api_views import *
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('about/', AboutView.as_view(), name='about'),
    # path("logout/", LogoutView.as_view(), name="logout"),
    path('open_weather/', OpenWeatherView.as_view(), name='open-weather'),
    path('weather_bit/', WeatherBitView.as_view(), name='weather-bit'),
    path('registration/register/', RegisterUser.as_view(), name='register'),
    path('registration/login/', LoginUser.as_view(), name='login'),
    path('registration/logout/', logout_user, name='logout'),
    path('profile/', Profile.as_view(), name='profile'),
    path('change_profile/', ChangeProfile.as_view(), name='change_profile'),

    path('api/v1/subscriptions/', SubscriptionAPIList.as_view(), name='subscriptions-list'),
    path('api/v1/subscriptions/<int:pk>/', SubscriptionAPIList.as_view(), name='one-subscription'),
    path('api/v1/cities/', CitiesListView.as_view(), name='cities-list'),
    path('api/v1/cities/<int:pk>/', CitiesListView.as_view(), name='one-city'),
    path('api/v1/get_weather/', GetWeather.as_view(), name='weather-list'),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

handler404 = pageNotFound