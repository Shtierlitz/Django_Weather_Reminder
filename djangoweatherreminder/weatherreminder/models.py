import json
import sys
import zoneinfo
from datetime import datetime

import pytz
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_celery_beat.models import  PeriodicTask, CrontabSchedule


class Service(models.TextChoices):
    open_weather = "OpenWeatherMap",
    weather_bit = "WeatherBit",


class User(AbstractUser):
    username = models.CharField(max_length=50, verbose_name="User name", unique=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ("id",)


class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="City", unique=True)
    users = models.ManyToManyField(User, through='Subscription', related_name='city_subscriptions')

    def __str__(self):
        return f'{self.name}'

def current_time():
    s = timezone.datetime.now()
    a = timezone.make_aware(s, pytz.timezone('UTC'))
    return a

class Subscription(models.Model):
    class Period(models.IntegerChoices):
        ONE = 1
        THREE = 3
        SIX = 6
        TWELVE = 12


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='subscriptions')
    period_notifications = models.IntegerField(choices=Period.choices)
    date_of_subscription = models.DateTimeField(default=current_time)
    service = models.TextField(choices=Service.choices)

    def __str__(self):
        # return f"{self.pk}"
        return f'{self.user} has a subscription on {self.service} since {self.date_of_subscription} ' \
               f'with period of notifications - {self.period_notifications} hours.'


class Weather(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100, verbose_name="City name", blank=True)
    service = models.TextField(choices=Service.choices)
    country_code = models.CharField(max_length=100, verbose_name="Country code", blank=True)
    coordinate = models.CharField(max_length=100, verbose_name="Coordinate", blank=True)
    temp = models.CharField(max_length=100, verbose_name="Temperature", blank=True)
    pressure = models.CharField(max_length=100, verbose_name="Pressure", blank=True)
    humidity = models.CharField(max_length=100, verbose_name="Humidity", blank=True)


class SubscriptionTask:
    def __init__(self, subscription):
        self.subscription = subscription

    def create_task(self):
        schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='*/'+str(self.subscription.period_notifications) if str(self.subscription.period_notifications) != '1' else '*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=zoneinfo.ZoneInfo('Europe/Kiev')
    )
        task = PeriodicTask.objects.filter(
            name=f'Send email with {self.subscription.service} with {self.subscription.city} to {self.subscription.user.email}').first()
        if task is not None:
            return
        task = PeriodicTask.objects.create(
            name=f'Send email with {self.subscription.service} with {self.subscription.city} to {self.subscription.user.email}',
            task='send_email_task',
            crontab=schedule,
            args=json.dumps([self.subscription.id]),
            start_time=timezone.now()
        )
        task.save()
        return

    def edit_task(self):
        task = PeriodicTask.objects.filter(name=f'Send email with {self.subscription.service} with {self.subscription.city} to {self.subscription.user.email}').first()

        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='*/'+str(self.subscription.period_notifications) if str(self.subscription.period_notifications) != '1' else '*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=zoneinfo.ZoneInfo('Europe/Kiev')
        )
        if task:
            task.crontab = schedule
            task.save()
        return

    def delete_task(self):
        task = PeriodicTask.objects.filter(name=f'Send email with {self.subscription.service} with {self.subscription.city} to {self.subscription.user.email}').first()
        if task is not None:
            task.delete()
        return


class WeatherTask:
    def __init__(self, subscription):
        self.subscription = subscription

    def create_task(self):
        """It is necessary to check if there is no another task doing the same
        and only then create new task"""
        task = PeriodicTask.objects.filter(
            name=f'Update weather for city {self.subscription.city.name} and service {self.subscription.service} every hour in database').first()
        if task is not None:
            return
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=zoneinfo.ZoneInfo('Europe/Kiev')
        )
        task = PeriodicTask.objects.create(
            name=f'Update weather for city {self.subscription.city.name} and service {self.subscription.service} every hour in database',
            task='get_weather_task',
            crontab=schedule,
            args=json.dumps([self.subscription.id]),
            start_time=timezone.now()
        )
        task.save()
        return

    def delete_subscription_weather_task(self):
        """Use in subscription "delete" apiView.
        In subscription apiView we need to check that this is a last subscription left on city
        with selected service and only then delete task."""

        city = City.objects.get(pk=self.subscription.city.id)
        subscriptions = Subscription.objects.filter(city=city, service=self.subscription.service)
        if len(subscriptions) == 1:
            task = PeriodicTask.objects.filter(
                name=f'Update weather for city {city.name} and service {self.subscription.service} every hour in database').first()
            if task is not None:
                task.delete()
        return

    def delete_city_weather_task(self):
        """Use in city "delete" apiView.
        In city apiView because of two services we need to check
        every subscription in delete cycle
        so it should avoid error if there is no such task."""
        task = PeriodicTask.objects.filter(
            name=f'Update weather for city {self.subscription.city.name} and service {self.subscription.service} every hour in database').first()
        if task is not None:
            task.delete()
        return

