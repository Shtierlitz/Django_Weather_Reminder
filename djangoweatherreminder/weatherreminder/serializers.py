from datetime import datetime

import environ
from rest_framework import serializers, status

from djangoweatherreminder.settings import OPEN_WEATHER_API_URL
from weatherreminder.models import Subscription, City, Service, User
from weatherreminder.utils import CityName, CheckCity
import pytz

env = environ.Env()
WEATHER_API_KEY = env('WEATHER_API_KEY')

class SubscriptionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    period_notifications = serializers.ChoiceField(choices=Subscription.Period.choices)
    date_of_subscription = serializers.DateTimeField(read_only=True)
    service = serializers.ChoiceField(choices=Service.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Check if update request, then mark 'service' field as not required
        if self.context.get('request') and self.context['request'].method in ['PUT', 'PATCH']:
            self.fields['service'].required = False
            self.fields['city'].required = False


    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.period_notifications = validated_data.get('period_notifications', instance.period_notifications)
        instance.date_of_subscription = datetime.now(tz=pytz._UTC())
        instance.save()
        return instance



class CitySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)

    def validate_name(self, value):
        """Before we create a new city in database we need to check and replace some symbols.
        Than needs to check if there already city in database and if it's not needs to
        check exists this city at all"""
        new_value = CityName(value).serializer()
        city = City.objects.filter(name=new_value).first()
        if city is None:
            if CheckCity(new_value, OPEN_WEATHER_API_URL, WEATHER_API_KEY).check_existing_OpenWeather_city():
                raise serializers.ValidationError("Such city does not exits")
            return new_value
        elif city is not None:
            raise serializers.ValidationError("City already exits")

    def create(self, validated_data):
        return City.objects.create(**validated_data)


class WeatherSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    city_name = serializers.CharField(max_length=100, read_only=True)
    service = serializers.ChoiceField(choices=Service.choices, read_only=True)
    country_code = serializers.CharField(max_length=100, read_only=True)
    coordinate = serializers.CharField(max_length=100, read_only=True)
    temp = serializers.CharField(max_length=100, read_only=True)
    pressure = serializers.CharField(max_length=100, read_only=True)
    humidity = serializers.CharField(max_length=100, read_only=True)

