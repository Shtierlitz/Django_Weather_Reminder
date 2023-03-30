from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from rest_framework import serializers
import re
import urllib
from rest_framework import status
import environ
import requests
from rest_framework.response import Response
from djangoweatherreminder.settings import OPEN_WEATHER_API_URL, WEATHER_BIT_API_URL
from .models import *

env = environ.Env()
WEATHER_API_KEY = env('WEATHER_API_KEY')
WEATHER_BIT_KEY = env('WEATHER_BIT_KEY')


class DataMixin:
    def get_user_context(self, **kwargs):
        context = kwargs
        return context


class CheckCity:
    def __init__(self, city_name, service_url, api_token):
        self.city_name = city_name
        self.service_url = service_url
        self.api_token = api_token

    def check_existing_OpenWeather_city(self):
        url = f'{self.service_url}?q={CityName(self.city_name).api()}&appid={self.api_token}'
        r = requests.get(url)
        print(r)
        return r.status_code != 200

    def check_existing_WeatherBit_city(self):
        url = f'{self.service_url}?key={self.api_token}&city={CityName(self.city_name).api()}'
        r = requests.get(url)
        print(r, 'bit')
        return r.status_code != 200


def delete_city_and_subscription(request, cities: list):
    new_list = [s.strip('[]') for s in cities]
    new_list = [s.split(', ') for s in new_list]
    if len(new_list) != 0:
        for c in new_list:
            service = c[-1]
            city = City.objects.filter(name=CityName(c[0]).serializer()).first()
            subscription = Subscription.objects.filter(user=request.user, city=city, service=service).first()
            SubscriptionTask(subscription).delete_task()
            WeatherTask(subscription).delete_subscription_weather_task()
            subscription.delete()

            all_subscriptions = Subscription.objects.filter(city=city)
            if len(all_subscriptions) == 0:
                city.users.remove(request.user)
                city.delete()


def str_to_dict(s):
    pattern = r"\[(.*?), (.*?), (.*?)\]"
    match = re.match(pattern, s)
    if match:
        return {match.group(1): [int(match.group(2)), match.group(3)]}
    else:
        return {}


def change_period(request, periods):
    new_list = [s.strip('[]') for s in periods]
    new_list = [s.split(', ') for s in new_list]
    for s in new_list:
        if s == ['Select hours']:
            pass
        else:
            user = User.objects.get(pk=request.user.id)
            city = City.objects.filter(name=CityName(s[0]).serializer(), users=user).first()
            subscription = Subscription.objects.filter(user=request.user, city=city, service=s[-1]).first()
            subscription.period_notifications = s[1]
            subscription.save()
            SubscriptionTask(subscription).edit_task()


class BaseWeather:
    def __init__(self, city=None):
        if city:
            if "_" in city or " " in city:
                self.city = str(city.replace("_", '%20').replace(" ", '%20'))
            else:
                self.city = city

    def __get_weather(self, token):
        pass

    def get_context_mixin(self, token, index=None):
        context = {}
        return context

    def create_weather(self, new_city, service, token):
        weather_data = self.get_context_mixin(token)
        return Weather.objects.create(
            city=new_city,
            city_name=CityName(weather_data['city']).serializer(),
            country_code=weather_data['country_code'],
            coordinate=weather_data['coordinate'],
            temp=weather_data['temp'],
            pressure=weather_data['pressure'],
            humidity=weather_data['humidity'],
            service=service,
        )


class OpenWeatherMap(BaseWeather):
    def __init__(self, city=None):
        super().__init__(city)
        self.OPEN_WEATHER_API_URL = OPEN_WEATHER_API_URL

    def __get_weather(self, token):
        source = urllib.request.urlopen(
            f'{self.OPEN_WEATHER_API_URL}?q={self.city}&appid={token}&units=metric').read()
        return json.loads(source)

    def get_context_mixin(self, token, index=None) -> dict:
        """Returns context dict directly from service in proper view"""
        list_of_data = self.__get_weather(token)
        # print(list_of_data, 'openw')
        city = CityName(self.city).view()
        if index:
            city = city.replace("_", " ")
        context_mixin = {
            'city': city,
            "country_code": str(list_of_data['sys']['country']),
            "coordinate": str(list_of_data['coord']['lon']) + ' ' + str(list_of_data['coord']['lat']),
            "temp": str(list_of_data['main']['temp']) + 'с',
            "pressure": str(list_of_data['main']['pressure']),
            "humidity": str(list_of_data['main']['humidity']) + '%'
        }
        return context_mixin

    def get_existing_weather_mixin(self, existing_city, index=None) -> dict:
        """Returns context dict from database"""
        weather_model = Weather.objects.filter(city=existing_city, service=Service.open_weather).first()
        city = CityName(weather_model.city_name).serializer()
        if index:
            city = city.replace("_", " ")
        context_mixin = {
            'city': city,
            "country_code": weather_model.country_code,
            "coordinate": weather_model.coordinate,
            "temp": weather_model.temp,
            "pressure": weather_model.pressure,
            "humidity": weather_model.humidity
        }
        return context_mixin


class CityName:
    def __init__(self, city):
        self.city = city

    def serializer(self):
        city = self.city.capitalize()
        if " " in city:
            city = city.replace(" ", '_')
        index = city.find("_") + 1
        city = city.replace(city[index], city[index].upper())
        return city

    def view(self):
        if "%20" in self.city:
            city = self.city.capitalize().replace("%20", " ")
        elif "_" in self.city:
            city = self.city.capitalize().replace("_", " ")
        else:
            city = self.city.capitalize()
        value = city.find(" ") + 1
        city = city.replace(city[value], city[value].upper())
        return city

    def api(self):
        city = self.city.capitalize()
        if " " in self.city:
            city = self.city.replace(" ", "%20")
        elif "_" in self.city:
            city = self.city.replace("_", "%20")
        index = city.find("%20") + 1
        city = city.replace(city[index], city[index].upper())
        return city


class WeatherBit(BaseWeather):
    def __init__(self, city=None):
        super().__init__(city)
        self.WEATHER_BIT_API_URL = WEATHER_BIT_API_URL

    def __get_weather(self, token):
        source = urllib.request.urlopen(
            f'{self.WEATHER_BIT_API_URL}?city={self.city}&key={token}&units=metric').read()
        return json.loads(source)

    def get_context_mixin(self, token, index=None):
        list_of_data = self.__get_weather(token)
        # print(list_of_data, 'weatherb')
        city = CityName(self.city).view()
        if index:
            city = city.replace("_", " ")
        context_mixin = {
            'city': city,
            "country_code": str(list_of_data['data'][0]['country_code']),
            "coordinate": str(list_of_data['data'][0]['lon']) + ' ' + str(list_of_data['data'][0]['lat']),
            "temp": str(list_of_data['data'][0]['temp']) + 'с',
            "pressure": str(list_of_data['data'][0]['pres']),
            "humidity": str(list_of_data['data'][0]['rh']) + '%'
        }
        return context_mixin

    def get_existing_weather_mixin(self, existing_city, index=None) -> dict:
        """Returns context dict from database"""
        weather_model = Weather.objects.filter(city=existing_city, service=Service.weather_bit).first()
        city = CityName(weather_model.city_name).serializer()
        if index:
            city = city.replace("_", " ")
        context_mixin = {
            'city': city,
            "country_code": weather_model.country_code,
            "coordinate": weather_model.coordinate,
            "temp": weather_model.temp,
            "pressure": weather_model.pressure,
            "humidity": weather_model.humidity
        }
        return context_mixin


def check_or_create_weather(city_model, city_name, service):
    weather = Weather.objects.filter(city_name=city_name, service=service).first()
    if weather:
        return
    if service == Service.open_weather:
        OpenWeatherMap(city=city_name).create_weather(city_model, service, WEATHER_API_KEY)
    else:
        WeatherBit(city=city_name).create_weather(city_model, service, WEATHER_BIT_KEY)


def check_period(period) -> int:
    try:
        period = int(period)
    except Exception as e:
        return 12
    return period


def subscription_dict(request, service) -> dict:
    subscription_lst = Subscription.objects.filter(user=request.user.id, service=service)
    dct = {}
    if len(subscription_lst) != 0:
        for subscription in subscription_lst:
            dct[CityName(subscription.city.name).view()] = [subscription.service, subscription.period_notifications]
    return dct





def check_existing_subscription(data):
    subscription = None
    try:
        subscription = Subscription.objects.filter(
            user=data['user'],
            city=data['city'],
            service=data['service'],
            period_notifications=data['period_notifications']
        ).first()
    except:
        return Response(
            {
                "city": [
                    "This field is required."
                ],
                "period_notifications": [
                    "This field is required."
                ],
                "service": [
                    "This field is required."
                ]
            }, status.HTTP_400_BAD_REQUEST
        )
    if subscription:
        return Response("Such subscription already exists!", status.HTTP_409_CONFLICT)
    return


def send_message(name, email, content):
    text = get_template("weatherreminder/message.html")
    html = get_template("weatherreminder/message.html")
    context = {
        'name': name,
        'email': email,
        'content': content
    }
    subject = "Weather notification"
    from_email = "rollbar1990@gmail.com"
    text_content = text.render(context)
    html_content = html.render(context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to=[email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def task_period_hours_change(period):
    if period == 3:
        return '*/'+period
    elif period == 6:
        return '*/'+period
    elif period == 12:
        return '*/'+period
    else:
        return '*'


