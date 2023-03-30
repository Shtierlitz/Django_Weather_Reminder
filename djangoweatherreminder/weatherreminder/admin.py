from django.contrib import admin
from .models import User, City, Subscription, Weather


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username')


class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'period_notifications', 'user', 'date_of_subscription', 'user', 'city')


class WeatherAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'service', 'country_code', 'coordinate', 'temp', 'pressure', 'humidity')


admin.site.register(User, UserAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Weather, WeatherAdmin)
