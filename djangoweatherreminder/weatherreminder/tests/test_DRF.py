from unittest.mock import patch

import pytz
from django.test import override_settings
from django.urls import reverse
from django.utils.datetime_safe import datetime
from rest_framework import status, serializers
from rest_framework.test import APITestCase
from weatherreminder.models import City, Subscription, Weather, User, Service
from weatherreminder.serializers import CitySerializer
from freezegun import freeze_time


class CityApiViewTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_name', password='test_pass', email='test@email.com')
        self.city = City.objects.create(name='New_York')
        self.data = {'name': "Las_Vegas"}

    def test_unauthorized(self):
        response = self.client.get(reverse("cities-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_cities_get_list(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("cities-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['users_cities']), 1)

    def test_fail_get_one_city(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("one-city", kwargs={'pk': 50}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_one_city(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("one-city", kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({'city': {'id': 1, 'name': 'New_York'}}, response.data)

    def test_unauthorized_create_city(self):
        response = self.client.post(reverse("cities-list"), self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_invalid_city_name(self):
        with self.assertRaisesMessage(serializers.ValidationError, "City already exits"):
            serializer = CitySerializer(data={'name': 'New_York'})
            serializer.is_valid(raise_exception=True)

    @patch('weatherreminder.utils.CheckCity.check_existing_OpenWeather_city')
    def test_wrong_city_serializer_fail(self, check_mock):
        check_mock.return_value = True
        with self.assertRaisesMessage(serializers.ValidationError, "Such city does not exits"):
            serializer = CitySerializer(data={'name': 'test_city'})
            serializer.is_valid(raise_exception=True)

    @patch('weatherreminder.utils.CheckCity.check_existing_OpenWeather_city')
    def test_create_city(self, check_mock):
        check_mock.return_value = False
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("cities-list"), self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'city': {'id': 2, 'name': 'Las_Vegas'}})

    def test_fail_create_city(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("cities-list"), {}, format='json')
        self.assertEqual(response.status_code, 400)
        expected_response = {'name': ['This field is required.']}
        self.assertDictEqual(response.data, expected_response)

    def test_delete_city_unauthorized(self):
        response = self.client.delete(reverse("one-city", kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_delete_city(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse("one-city", kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_wrong_delete_city(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse("one-city", kwargs={'pk': 50}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WeatherApiViewTests(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_name', password='test_pass', email='test@email.com')
        self.city = City.objects.create(name='New_York')
        self.weather = Weather.objects.create(
            city=self.city,
            city_name=self.city.name,
            service="OpenWeatherMap",
            country_code='US',
            coordinate='-74.006 40.7143',
            temp='14.6с',
            pressure='1028',
            humidity='21%'
        )

    def test_unauthorized(self):
        response = self.client.get(reverse("weather-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_cities_get_list(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("weather-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['weather_in_DB']), 1)


class SubscriptionApiView(APITestCase):
    @override_settings(USE_TZ=True)
    @freeze_time('2023-03-21T00:00:00', tz_offset=-2)
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_name', password='test_pass', email='test@email.com')
        self.city = City.objects.create(name='New_York')
        self.subscription = Subscription.objects.create(
            user=self.user,
            city=self.city,
            period_notifications='1',
            service=Service.open_weather,
        )
        self.data = {
            'user': 1,
            'city': 1,
            'period_notifications': 1,
            'service': Service.weather_bit
        }
        tz = pytz.timezone('Europe/Moscow')
        self.date_of_subscription = datetime.now(tz)
        self.date_of_subscription = self.date_of_subscription.astimezone(pytz.utc)
        self.fake_weather = {'city': 'Lublin', 'country_code': 'US', 'coordinate': '-115.1372 36.175', 'temp': '9.08с',
                             'pressure': '1019', 'humidity': '62%'}

    @freeze_time('2023-03-21T00:00:00', tz_offset=-2)
    def test_get_one_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("one-subscription", kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({'subscription': {'id': 1, 'user': self.user.id, 'city': self.city.id,
                                           'period_notifications': 1,
                                           'date_of_subscription': '2023-03-21T00:00:00+02:00',
                                           'service': 'OpenWeatherMap'}}, response.data)

    @override_settings(USE_TZ=True)
    @patch('weatherreminder.utils.WeatherBit.get_context_mixin')
    @freeze_time('2023-03-21T00:00:00', tz_offset=-2)
    def test_post_subscription(self, mixin_mock):
        self.fake_weather['city'] = 'New_York'
        mixin_mock.return_value = self.fake_weather
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('subscriptions-list'), self.data, format='json')
        self.assertEqual({'subscription': {'id': 2, 'user': 1, 'city': 1, 'period_notifications': 1,
                                           'date_of_subscription': '2023-03-21T00:00:00+02:00',
                                           'service': 'WeatherBit'}}, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Subscription.objects.all()), 2)

    def test_get_unauthorized(self):
        response = self.client.get(reverse("subscriptions-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_get_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse('subscriptions-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['users_cities']), 1)

    def test_fail_get_one_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("one-subscription", kwargs={'pk': 50}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_post_unauthorized(self):
        response = self.client.post(reverse('subscriptions-list'), self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_post_subscription_pk(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('one-subscription', kwargs={'pk': 50}))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, "Method POST got an unexpected keyword argument 'pk'")

    def test_post_no_data_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse('subscriptions-list'), {}, format='json')
        self.assertEqual(response.status_code, 400)
        expected_response = {'city': ['This field is required.'], 'period_notifications': ['This field is required.'],
                             'service': ['This field is required.']}
        self.assertDictEqual(response.data, expected_response)

    def test_put_unauthorized(self):
        response = self.client.put(reverse('one-subscription', kwargs={'pk': 1}), {"period_notifications": 3},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    @override_settings(USE_TZ=True)
    @freeze_time('2023-03-21T00:00:00', tz_offset=-2)
    def test_put_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse('one-subscription', kwargs={'pk': 1}), {"period_notifications": 3},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual({'subscription': {'id': 1, 'user': 1, 'city': 1, 'period_notifications': 3,
                                           'date_of_subscription': '2023-03-21T00:00:00+02:00',
                                           'service': 'OpenWeatherMap'}}, response.data)

    def test_put_fail_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(reverse('one-subscription', kwargs={'pk': 50}), {"period_notifications": 3},
                                   format='json')
        self.assertEqual(response.data, {'error': 'Object does not exist'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_subscription_unauthorized(self):
        response = self.client.delete(reverse('one-subscription', kwargs={'pk': 1}), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_fail_delete_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse('one-subscription', kwargs={'pk': 50}), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'error': 'Such city does not exist to delete!'})

    def test_delete_subscription(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse('one-subscription', kwargs={'pk': 1}), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {'subscription': 'delete subscription 1'})

