
from celery import shared_task

from weatherreminder.models import Subscription, Weather, City
from weatherreminder.utils import send_message, OpenWeatherMap, WeatherBit, CityName
import environ
env = environ.Env()


@shared_task(name="send_email_task")
def send_email_task(sub_id):
    subscription = Subscription.objects.get(pk=sub_id)
    weather = Weather.objects.filter(city_id=subscription.city.id, service=subscription.service).first()
    city_name = CityName(subscription.city.name).view()
    content = f"<p>Period of notifications : every {subscription.period_notifications} hours</p><hr>" \
              f"Service: {subscription.service}<hr>" \
              f"Country code: {weather.country_code}<hr>" \
              f"Coordinate: {weather.coordinate}<hr>" \
              f"Temperature: {weather.temp}<hr>" \
              f"Pressure: {weather.pressure}<hr>" \
              f"Humidity: {weather.humidity}<hr>"
    send_message(city_name, subscription.user.email, content)


@shared_task(name="get_weather_task")
def get_weather_task(sub_id):
    subscription = Subscription.objects.get(pk=sub_id)
    city = City.objects.get(pk=subscription.city.id)
    weather = Weather.objects.filter(city=city, service=subscription.service).first()
    if subscription.service == "OpenWeatherMap":
        weather_data = OpenWeatherMap(city.name).get_context_mixin(token=env('WEATHER_API_KEY'))
    else:
        weather_data = WeatherBit(city.name).get_context_mixin(env('WEATHER_BIT_KEY'))
    weather.temp = weather_data['temp']
    weather.humidity = weather_data['humidity']
    weather.pressure = weather_data['pressure']
    weather.coordinate = weather_data['coordinate']
    weather.country_code = weather_data['country_code']
    weather.save()


