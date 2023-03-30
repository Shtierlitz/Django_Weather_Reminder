from unittest.mock import patch

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status
from weatherreminder.models import User, City, Subscription, Weather, Service


class TestOpenWeatherMapViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='test_username_1', password='test_password', email='test_email_1@mail.com')
        self.user1.save()
        self.user2 = User.objects.create_user(username='test_username_2', password='test_password_2', email='test_email_2@mail.com')
        self.user2.save()
        self.city1 = City.objects.create(name='New_York')
        self.city2 = City.objects.create(name='London')
        self.subscription_1 = Subscription.objects.create(
            user=self.user1,
            city=self.city1,
            period_notifications=Subscription.Period.ONE,
            service=Service.open_weather
        )

        self.weather = Weather.objects.create(
            city=self.city1,
            city_name=self.city1.name,
            service="OpenWeatherMap",
            country_code='US',
            coordinate='-74.006 40.7143',
            temp='14.6с',
            pressure='1028',
            humidity='21%'
        )

        self.client.login(username='test_username_1', password='test_password')
        self.fake_weather = {'city': 'Lublin', 'country_code': 'US', 'coordinate': '-115.1372 36.175', 'temp': '9.08с',
                             'pressure': '1019', 'humidity': '62%'}


    def test_homepage(self):
        response = self.client.get(reverse('home'))
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/index.html')

    def test_OpenWeatherView_get(self):
        response = self.client.get(reverse('open-weather'))
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/open_weather.html')
#
    def test_OpenWeatherView_empty_post(self):
        response = self.client.post(reverse('open-weather'), data={})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/open_weather.html')

    @patch('weatherreminder.views.CheckCity.check_existing_OpenWeather_city')
    def test_OpenWeatherView_post_city_not_exists(self, check_mock):
        check_mock.return_data = False
        response = self.client.post(reverse('open-weather'), data={'city': 'asd'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/open_weather.html')

    @patch('weatherreminder.views.OpenWeatherMap.get_context_mixin')
    def test_OpenWeatherView_post_existing_subscription(self, mixin_mock):
        self.fake_weather['city'] = self.city1.name
        mixin_mock.return_value = self.fake_weather
        response = self.client.post(reverse('open-weather'),
                                    data={'period': 1, 'service': "OpenWatherMap",
                                          'city': self.city1.name})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/open_weather.html')

    @patch('weatherreminder.views.OpenWeatherMap.get_context_mixin')
    def test_OpenWeatherView_post_existing_city_no_subscription(self, mixin_mock):
        self.fake_weather['city'] = 'London'
        mixin_mock.return_value = self.fake_weather
        response = self.client.post(reverse('open-weather'),
                                    data={'period': 6, 'service': "OpenWatherMap",
                                          'city': 'London'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/open_weather.html')

    @patch('weatherreminder.views.OpenWeatherMap.get_context_mixin')
    @patch('weatherreminder.views.CheckCity.check_existing_OpenWeather_city')
    def test_OpenWeatherView_new_city_new_subscription(self, check_mock, context_mock):
        self.fake_weather['city'] = "Las_Vegas"
        check_mock.return_value = False
        context_mock.return_value = self.fake_weather
        response = self.client.post(reverse('open-weather'),
                                    data={'period': 1, 'service': "OpenWatherMap",
                                          'city': "Las_Vegas"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/open_weather.html')

    @patch('weatherreminder.views.CheckCity.check_existing_OpenWeather_city')
    @patch('weatherreminder.utils.OpenWeatherMap.get_context_mixin')
    def test_OpenWeatherView_to_many_requests(self, context_mixin, check_mock):
        check_mock.return_value = False
        context_mixin.return_value = status.HTTP_429_TOO_MANY_REQUESTS
        response = self.client.post(reverse('open-weather'), data={'period': 1, 'service': "OpenWatherMap",
                                          'city': "Las_Vegas"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class TestWeatherBitViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='test_username_1', password='test_password',
                                              email='test_email_1@mail.com')
        self.user1.save()

        self.user2 = User.objects.create_user(username='test_username_2', password='test_password_2',
                                              email='test_email_2@mail.com')
        self.user2.save()
        self.city2 = City.objects.create(name='London')
        self.subscription_2 = Subscription.objects.create(
            user=self.user2,
            city=self.city2,
            period_notifications=Subscription.Period.ONE,
            service=Service.weather_bit
        )
        self.weather_bit = Weather.objects.create(
            city=self.city2,
            city_name=self.city2.name,
            service="WeatherBit",
            country_code='US',
            coordinate='-74.006 40.7143',
            temp='14.6с',
            pressure='1028',
            humidity='21%'
        )
        self.client.login(username='test_username_2', password='test_password_2')
        self.fake_weather = {'city': 'Lublin', 'country_code': 'US', 'coordinate': '-115.1372 36.175', 'temp': '9.08с', 'pressure': '1019', 'humidity': '62%'}

    def test_WeatherBitView_get(self):
        response = self.client.get(reverse('weather-bit'))
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/weather_bit.html')

    def test_WeatherBitView_empty_post(self):
        response = self.client.post(reverse('weather-bit'), data={})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/weather_bit.html')

    @patch('weatherreminder.views.CheckCity.check_existing_OpenWeather_city')
    def test_WeatherBitView_post_city_not_exists(self, status_mock):
        status_mock.return_value = True
        self.client.login(username='test_username_2', password='test_password_2')
        response = self.client.post(reverse('weather-bit'), data={'city': 'unknown_city'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/weather_bit.html')

    def test_WeatherBitView_post_existing_city(self):
        self.client.login(username='test_username_1', password='test_password')
        response = self.client.post(reverse('weather-bit'),
                                    data={'period': 3, 'service': "WeatherBit",
                                          'city': 'London'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/weather_bit.html')

    def test_WeathrBitView_post_existing_subscription(self):
        self.client.login(username='test_username_2', password='test_password_2')
        response = self.client.post(reverse('weather-bit'),
                                    data={'period': 1, 'service': "WeatherBit",
                                          'city': self.city2.name})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/weather_bit.html')

    @patch('weatherreminder.views.CheckCity.check_existing_OpenWeather_city')
    @patch('weatherreminder.views.WeatherBit.get_context_mixin')
    def test_WeatherBitView_new_city_new_subscription(self, context_mock, status_mock):
        context_mock.return_value = self.fake_weather
        status_mock.return_value = False
        response = self.client.post(reverse('weather-bit'),
                                    data={'period': 3, 'service': "WeatherBit",
                                          'city': "Lublin"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        self.assertTemplateUsed(response, 'weatherreminder/weather_bit.html')
        self.assertEqual(len(Weather.objects.all()), 2)
        self.assertEqual(Weather.objects.get(pk=2).city_name, 'Lublin')

    @patch('weatherreminder.views.CheckCity.check_existing_OpenWeather_city')
    @patch('weatherreminder.utils.WeatherBit.get_context_mixin')
    def test_WeatherBitView_to_many_requests(self, context_mixin, status_mock):
        context_mixin.return_value = status.HTTP_429_TOO_MANY_REQUESTS
        status_mock.return_value = False
        response = self.client.post(reverse('weather-bit'), data={'period': 1, 'service': "WeatherBit",
                                          'city': "Las_Vegas"})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)



class TestOther(TestCase):

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='test_username_1', password='test_password',
                                              email='test_email_1@mail.com')
        self.city1 = City.objects.create(name='New_York')

        self.subscription_1 = Subscription.objects.create(
            user=self.user1,
            city=self.city1,
            period_notifications=Subscription.Period.ONE,
            service=Service.open_weather
        )
        self.weather = Weather.objects.create(
            city=self.city1,
            city_name=self.city1.name,
            service="OpenWeatherMap",
            country_code='US',
            coordinate='-74.006 40.7143',
            temp='14.6с',
            pressure='1028',
            humidity='21%'
        )
        self.client.login(username='test_username_1', password='test_password')


    def test_profile(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/profile.html')

    def test_change_profile_get(self):
        response = self.client.get(reverse('change_profile'))
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/change_profile.html')

    def test_profile_post_success(self):
        response = self.client.post(reverse('change_profile'), data={
            'username': 'New_username',
            'email': 'new_mail@mail.com'

        }, format='json')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')
        new_user = User.objects.get(pk=1)
        self.assertEqual(new_user.username, 'New_username')
        self.assertEqual(new_user.email, 'new_mail@mail.com')

    def test_profile_post_period(self):
        response = self.client.post(reverse('change_profile'), data={
            'username': 'test_username_1',
            'email': 'test_email_1@mail.com',
            'period': ['[New_York, 3, OpenWeatherMap]']
        }, format='json')
        self.assertEqual(response.status_code, 302)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        subscription = Subscription.objects.filter(period_notifications=3, user=self.user1, city=self.city1).first()
        self.assertEqual(subscription.period_notifications, 3)

    def test_profile_post_cities(self):
        response = self.client.post(reverse('change_profile'), data={
            'username': 'test_username_1',
            'email': 'test_email_1@mail.com',
            'cities': ['[New_York, 1, OpenWeatherMap]']
        }, format='json')
        self.assertEqual(response.status_code, 302)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertEqual(len(City.objects.all()), 0)

    def test_profile_post_fail(self):
        response = self.client.post(reverse('change_profile'), {}, format='json')
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/change_profile.html')

    def test_login_get(self):
        response = self.client.get(reverse('change_profile'))
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/change_profile.html')

    def test_login_post_fail(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'test_username_1',
            'password': 'asd'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertFalse(self.client.login(username='test_username_1', password='asd'))

    def test_login_post_success(self):
        User.objects.create_user(username="fake_user", password='fake_password', email='fake_pass@com.ua')
        response = self.client.post(reverse('login'), {
            'username': 'fake_user',
            'password': 'fake_password'
        }, format='json')
        self.assertEqual(response.status_code, 302)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTrue(self.client.login(username='fake_user', password='fake_password'))

    def test_registration_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_register_post(self):
        self.client.logout()
        self.assertEqual(len(User.objects.all()), 1)
        response = self.client.post(reverse('register'), {
            'username': 'test_username_3',
            'password1': 'new_test_pass_007',
            'password2': 'new_test_pass_007',
            'email': 'new_test_mail@mai.com'
        }, format='json')
        self.assertEqual(response.status_code, 302)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertEqual(len(User.objects.all()), 2)

    def test_register_post_empty(self):
        self.client.logout()
        self.assertEqual(len(User.objects.all()), 1)
        response = self.client.post(reverse('register'), {}, format='json')
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertEqual(len(User.objects.all()), 1)

    def test_AboutView(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        self.assertTemplateUsed(response, 'weatherreminder/about.html')