from django.test import TestCase, Client, override_settings
from freezegun.api import freeze_time

from weatherreminder.models import User, City, Subscription, Service, Weather


class TestModels(TestCase):
    @override_settings(USE_TZ=True)
    @freeze_time('2023-03-21T00:00:00.00000+02:00')
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(username="test_username", password='test_pass', email='test@mail.com')
        self.city = City.objects.create(name='New_York')
        self.subsciption = Subscription.objects.create(
            user=self.user,
            city=self.city,
            period_notifications=1,
            service=Service.open_weather
        )
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

    def test_User_model(self):
        self.test_user = User.objects.get(pk=1)
        self.assertEqual(self.test_user.username, 'test_username')
        self.assertEqual(self.test_user.email, 'test@mail.com')

    def test_City_model(self):
        self.test_city = City.objects.get(pk=1)
        self.assertEqual(self.city.name, 'New_York')
        self.assertEqual(len(self.city.users.all()), 1)

    def test_Subscription_model(self):
        self.test_subscription = Subscription.objects.get(pk=1)
        self.assertEqual(self.test_subscription.user, self.user)
        self.assertEqual(self.test_subscription.city, self.city)
        self.assertEqual(self.test_subscription.period_notifications, 1)
        self.assertEqual(self.test_subscription.service, Service.open_weather)

    def test_Weather_model(self):
        self.test_weather = Weather.objects.get(pk=1)
        self.assertEqual(self.test_weather.city, self.city)
        self.assertEqual(self.test_weather.city_name, 'New_York')
        self.assertEqual(self.test_weather.service, Service.open_weather)
        self.assertEqual(self.test_weather.country_code, 'US')
        self.assertEqual(self.test_weather.coordinate, '-74.006 40.7143')
        self.assertEqual(self.test_weather.temp, '14.6с')
        self.assertEqual(self.test_weather.pressure, '1028')
        self.assertEqual(self.test_weather.humidity, '21%')





