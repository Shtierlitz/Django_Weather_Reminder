
from weatherreminder.utils import change_period, \
    check_period, delete_city_and_subscription, subscription_dict, \
    OpenWeatherMap, CityName, CheckCity, WeatherBit

from django.contrib.auth import logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render, redirect, get_object_or_404
import environ
from django.views import View
from django.views.generic import CreateView, ListView

from djangoweatherreminder.settings import OPEN_WEATHER_API_URL, WEATHER_BIT_API_URL
from weatherreminder.forms import RegisterUserForm, LoginUserForm, ChangeProfileForm
from weatherreminder.models import Subscription, User, City, Service, Weather, SubscriptionTask, WeatherTask
from weatherreminder.utils import DataMixin

env = environ.Env()
WEATHER_API_KEY = env('WEATHER_API_KEY')
WEATHER_BIT_KEY = env('WEATHER_BIT_KEY')


def home(request):
    if request.method == 'POST':
        city = request.POST.get('city')
        token = request.POST.get('token')
        try:
            context = OpenWeatherMap(city=city).get_context_mixin(token, index=True)
        except:
            context = {'error': True}
        return render(request, 'weatherreminder/index.html', context)
    context = {"user": request.user}
    return render(request, 'weatherreminder/index.html', context)


class OpenWeatherView(LoginRequiredMixin, DataMixin, View):
    model = Subscription
    template_name = 'weatherreminder/open_weather.html'

    def get(self, request):
        context = self.get_user_context()
        context['title'] = "OpenWeatherMap service"
        context['user'] = request.user
        return render(request, self.template_name, context=context)

    def post(self, request):
        user = request.user
        context = self.get_user_context()
        context['title'] = "OpenWeatherMap service"
        context['user'] = user
        city = request.POST.get('city')
        period = request.POST.get('period')
        service = Service.open_weather
        try:
            existing_city = City.objects.filter(
                    name__iexact=CityName(city).serializer()).first()
        except:
            context['error'] = True
            return render(request, self.template_name, context, status=302)
        if not existing_city:
            if CheckCity(city, OPEN_WEATHER_API_URL, WEATHER_API_KEY).check_existing_OpenWeather_city():
                context['error'] = True
                return render(request, self.template_name, context, status=302)
            new_city = City.objects.create(name=CityName(city).serializer())
            subscription = Subscription.objects.create(
                user=user,
                city=new_city,
                period_notifications=check_period(period),
                service=service
            )
            new_city.users.add(user)
            new_city.save()
            try:
                OpenWeatherMap(city=city).create_weather(new_city, service, WEATHER_API_KEY)
            except:
                context['too_many'] = True
                return render(request, self.template_name, context, status=429)
            SubscriptionTask(subscription).create_task()
            WeatherTask(subscription).create_task()
            try:
                context_mixin = OpenWeatherMap(city=city).get_context_mixin(WEATHER_API_KEY, index=True)
            except:
                context['to_many'] = True
                return render(request, self.template_name, context, status=429)
            context.update(context_mixin)
            return render(request, self.template_name, context, status=200)
        else:
            existing_subscription = Subscription.objects.filter(city=existing_city, user=user, service=Service.open_weather).first()
            if existing_subscription is not None:
                existing_subscription.period_notifications = period if period != "Select period" else 12
                existing_subscription.save()
                context_mixin = OpenWeatherMap(city=city).get_existing_weather_mixin(existing_city, index=True)
                SubscriptionTask(existing_subscription).create_task()
                WeatherTask(existing_subscription).create_task()
                context.update(context_mixin)
                if context['user'] == request.user:
                    context['exists'] = True
                return render(request, self.template_name, context, status=302)
            subscription = Subscription.objects.create(
                user=user,
                city=existing_city,
                period_notifications=check_period(period),
                service=service
            )
            existing_city.users.add(user)
            existing_city.save()
            weather = Weather.objects.filter(city_name=existing_city.name, service=service).first()
            if not weather:
                try:
                    OpenWeatherMap(city=city).create_weather(existing_city, service, WEATHER_API_KEY)
                    context_mixin = OpenWeatherMap(city=city).get_context_mixin(WEATHER_API_KEY)
                except:
                    context['to_many'] = True
                    return render(request, self.template_name, context, status=429)
            else:
                context_mixin = OpenWeatherMap().get_existing_weather_mixin(existing_city, index=True)
            SubscriptionTask(subscription).create_task()
            WeatherTask(subscription).create_task()
            context.update(context_mixin)
            return render(request, self.template_name, context, status=200)


class WeatherBitView(LoginRequiredMixin, DataMixin, View):
    model = Subscription
    template_name = 'weatherreminder/weather_bit.html'

    def get(self, request):
        context = self.get_user_context()
        context['title'] = "OpenWeatherMap service"
        context['user'] = request.user
        return render(request, self.template_name, context=context)

    def post(self, request):
        user = request.user
        context = self.get_user_context()
        context['title'] = "WeatherBit service"
        context['user'] = user
        city = request.POST.get('city')
        period = request.POST.get('period')
        service = Service.weather_bit
        try:
            existing_city = City.objects.filter(
                name__iexact=CityName(city).serializer()).first()
        except:
            context['error'] = True
            return render(request, self.template_name, context, status=302)
        if not existing_city:
            if CheckCity(city, OPEN_WEATHER_API_URL, WEATHER_API_KEY).check_existing_OpenWeather_city():
                context['error'] = True
                return render(request, self.template_name, context, status=302)
            new_city = City.objects.create(name=CityName(city).serializer())
            subscription = Subscription.objects.create(
                user=user,
                city=new_city,
                period_notifications=check_period(period),
                service=service
            )
            new_city.users.add(user)
            new_city.save()
            try:
                WeatherBit(city=city).create_weather(new_city, service, WEATHER_BIT_KEY)
            except:
                context['to_many'] = True
                return render(request, self.template_name, context, status=429)
            SubscriptionTask(subscription).create_task()
            WeatherTask(subscription).create_task()
            context_mixin = WeatherBit(city=city).get_context_mixin(WEATHER_BIT_KEY, index=True)
            context.update(context_mixin)
            return render(request, self.template_name, context, status=200)
        else:
            existing_subscription = Subscription.objects.filter(city=existing_city, user=user, service=Service.weather_bit).first()
            if existing_subscription is not None:
                existing_subscription.period_notifications = period if period != "Select period" else 12
                existing_subscription.save()
                context_mixin = WeatherBit(city=city).get_existing_weather_mixin(existing_city, index=True)
                SubscriptionTask(existing_subscription).create_task()
                WeatherTask(existing_subscription).create_task()
                context.update(context_mixin)
                if context['user'] == request.user:
                    context['exists'] = True
                return render(request, self.template_name, context, status=302)
            subscription = Subscription.objects.create(
                user=user,
                city=existing_city,
                period_notifications=check_period(period),
                service=service
            )
            existing_city.users.add(user)
            existing_city.save()
            weather = Weather.objects.filter(city_name=existing_city.name, service=service).first()
            if not weather:
                try:
                    WeatherBit(city=city).create_weather(existing_city, service, WEATHER_BIT_KEY)
                    context_mixin = WeatherBit(city=city).get_context_mixin(WEATHER_BIT_KEY)
                except:
                    context['to_many'] = True
                    return render(request, self.template_name, context, status=429)
            else:
                context_mixin = WeatherBit().get_existing_weather_mixin(existing_city, index=True)
            SubscriptionTask(subscription).create_task()
            WeatherTask(subscription).create_task()
            context.update(context_mixin)
            return render(request, self.template_name, context, status=200)


class RegisterUser(DataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'registration/register.html'

    # success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_mixin = self.get_user_context(title="Create an account")
        context.update(context_mixin)
        return context

    def form_valid(self, form):
        """Auto validation if successful registration"""
        user = form.save()
        login(self.request, user)
        return redirect('home')


class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'registration/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context_mixin = self.get_user_context(title='Sign in')
        context.update(context_mixin)
        return context

    # def get_success_url(self):
    #     return reverse_lazy('home')


class Profile(LoginRequiredMixin, DataMixin, ListView):
    model = User
    template_name = 'weatherreminder/profile.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = get_object_or_404(User, pk=self.request.user.pk)
        context_mixin = self.get_user_context(title=f"Yours profile: {context['user']}")
        context_mixin['subscription'] = Subscription.objects.filter(user=self.request.user.id).first()
        context_mixin['open_weather'] = subscription_dict(self.request, Service.open_weather)
        context_mixin['weather_bit'] = subscription_dict(self.request, Service.weather_bit)
        context.update(context_mixin)
        return context


class ChangeProfile(LoginRequiredMixin, DataMixin, View):
    post_form = ChangeProfileForm
    template_name = 'weatherreminder/change_profile.html'

    def get(self, request):
        user = request.user
        initial_data = {
            'username': user.username,
            'email': user.email,
        }
        context = self.get_user_context()
        context_mixin = self.get_user_context(title=f"Change profile")
        context['form'] = self.post_form(initial=initial_data)
        context['user'] = get_object_or_404(User, pk=self.request.user.pk)
        context.update(context_mixin)
        context['open_weather'] = subscription_dict(request, Service.open_weather)
        context['weather_bit'] = subscription_dict(request, Service.weather_bit)

        return render(request, self.template_name, context=context)

    def post(self, request):
        settings_exists = get_object_or_404(User, pk=request.user.pk)
        settings_form = self.post_form(request.POST, instance=settings_exists)
        context = self.get_user_context()
        context['form'] = settings_form
        context['title'] = 'Edit profile'
        context['user'] = get_object_or_404(User, pk=self.request.user.pk)
        cities = request.POST.getlist('cities')
        period = request.POST.getlist('period')
        if settings_form.is_valid():
            change_period(request, period)
            delete_city_and_subscription(request, cities)
            settings_form.save()
            return redirect('profile')
        else:
            settings_form = self.post_form(request.POST)
            context['form'] = settings_form
        return render(request, self.template_name, context=context)

class AboutView(LoginRequiredMixin, DataMixin, ListView):
    model = User
    template_name = 'weatherreminder/about.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = get_object_or_404(User, pk=self.request.user.pk)
        context['title'] = "About Weather Reminder"
        return context


def logout_user(request):
    logout(request)
    return redirect('home')


def pageNotFound(request, exception):
    return HttpResponseNotFound("<h1>Page not found!</h1>")


def serverError(request):
    return HttpResponseServerError("<h1>Server error!</h1>")
