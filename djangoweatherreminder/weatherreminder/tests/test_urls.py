from django.test import SimpleTestCase
from django.urls import reverse, resolve
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from weatherreminder.api_views import *
from weatherreminder.views import *


class TestUrls(SimpleTestCase):

    def test_home(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func, home)

    def test_about(self):
        url = reverse('about')
        self.assertEqual(resolve(url).func.view_class, AboutView)

    def test_logout(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func, logout_user)

    def test_open_weather(self):
        url = reverse('open-weather')
        self.assertEqual(resolve(url).func.view_class, OpenWeatherView)

    def test_weather_bit(self):
        url = reverse('weather-bit')
        self.assertEqual(resolve(url).func.view_class, WeatherBitView)

    def test_register(self):
        url = reverse('register')
        self.assertEqual(resolve(url).func.view_class, RegisterUser)

    def test_login(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class, LoginUser)

    def test_profile(self):
        url = reverse('profile')
        self.assertEqual(resolve(url).func.view_class, Profile)

    def test_change_profile(self):
        url = reverse('change_profile')
        self.assertEqual(resolve(url).func.view_class, ChangeProfile)

    def test_API_subscriptions_list(self):
        url = reverse('subscriptions-list')
        self.assertEqual(resolve(url).func.view_class, SubscriptionAPIList)

    def test_API_one_subscription(self):
        url = reverse('one-subscription', args=[1])
        self.assertEqual(resolve(url).func.view_class, SubscriptionAPIList)

    def test_API_cities_list(self):
        url = reverse('cities-list')
        self.assertEqual(resolve(url).func.view_class, CitiesListView)

    def test_API_one_city(self):
        url = reverse('one-city', args=[1])
        self.assertEqual(resolve(url).func.view_class, CitiesListView)

    def test_API_get_weather(self):
        url = reverse('weather-list')
        self.assertEqual(resolve(url).func.view_class, GetWeather)

    def test_API_token(self):
        url = reverse('token_obtain_pair')
        self.assertEqual(resolve(url).func.view_class, TokenObtainPairView)

    def test_API_token_refresh(self):
        url = reverse('token_refresh')
        self.assertEqual(resolve(url).func.view_class, TokenRefreshView)

    def test_API_token_verify(self):
        url = reverse('token_verify')
        self.assertEqual(resolve(url).func.view_class, TokenVerifyView)

