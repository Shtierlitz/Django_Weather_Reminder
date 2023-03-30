
from rest_framework import status
from rest_framework.authentication import SessionAuthentication

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
import environ

from weatherreminder.models import *
from weatherreminder.serializers import SubscriptionSerializer, CitySerializer, WeatherSerializer
from weatherreminder.utils import check_or_create_weather, check_existing_subscription

env = environ.Env()
WEATHER_API_KEY = env('WEATHER_API_KEY')
WEATHER_BIT_KEY = env('WEATHER_BIT_KEY')


class SubscriptionAPIList(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        request.data['user'] = User.objects.get(pk=request.user.id).id
        pk = kwargs.get("pk", None)
        if not pk:
            subscriptions = Subscription.objects.filter(user=request.user.id)
            return Response({'users_cities': SubscriptionSerializer(subscriptions, many=True).data}, status.HTTP_200_OK)
        try:
            subscription = Subscription.objects.get(pk=pk)
        except:
            return Response({"error": "Such subscription does not exist"}, status.HTTP_404_NOT_FOUND)
        return Response({"subscription": SubscriptionSerializer(subscription).data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if kwargs.get("pk", None):
            return Response("Method POST got an unexpected keyword argument 'pk'", status.HTTP_405_METHOD_NOT_ALLOWED)
        request.data['user'] = User.objects.get(pk=request.user.id).id
        check_existing_subscription(request.data)
        subscription_serializer = SubscriptionSerializer(data=request.data)
        subscription_serializer.is_valid(raise_exception=True)
        subscription_serializer.save()
        city = City.objects.get(pk=request.data['city'])
        check_or_create_weather(city, city.name, subscription_serializer.data['service'])
        city.users.add(request.user)
        city.save()
        subscription = Subscription.objects.get(pk=subscription_serializer.data['id'])
        SubscriptionTask(subscription).create_task()
        WeatherTask(subscription).create_task()
        return Response({"subscription": subscription_serializer.data},
                        status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        context = {'request': request}
        request.data['user'] = User.objects.get(pk=request.user.id).id
        pk = kwargs.get("pk", None)
        if not pk:
            return Response({"error": "Method PUT is not allowed"}, status.HTTP_405_METHOD_NOT_ALLOWED)
        try:
            instance = Subscription.objects.get(pk=pk)
        except:
            return Response({"error": "Object does not exist"}, status.HTTP_404_NOT_FOUND)
        subscription_serializer = SubscriptionSerializer(data=request.data, instance=instance,  context=context)
        subscription_serializer.is_valid(raise_exception=True)
        subscription_serializer.save()
        subscription = Subscription.objects.get(pk=subscription_serializer.data['id'])
        SubscriptionTask(subscription).edit_task()
        return Response({"subscription": subscription_serializer.data}, status=status.HTTP_205_RESET_CONTENT)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return Response({"error": "Method delete is not allowed!"}, status.HTTP_405_METHOD_NOT_ALLOWED)
        try:
            subscription = Subscription.objects.get(pk=pk)
        except:
            return Response({"error": "Such city does not exist to delete!"}, status.HTTP_404_NOT_FOUND)
        SubscriptionTask(subscription).delete_task()
        WeatherTask(subscription).delete_subscription_weather_task()
        subscription.delete()
        return Response({"subscription": "delete subscription " + str(pk)}, status=status.HTTP_204_NO_CONTENT)




class CitiesListView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            cities = City.objects.all()
            return Response({'users_cities': CitySerializer(cities, many=True).data}, status.HTTP_200_OK)
        try:
            city = City.objects.get(pk=pk)
        except:
            return Response({"error": "Such sity does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"city": CitySerializer(city).data}, status=status.HTTP_200_OK)


    def post(self, request):
        request.data['user'] = User.objects.get(pk=request.user.id).id
        city_serializer = CitySerializer(data=request.data)
        city_serializer.is_valid(raise_exception=True)
        city_serializer.save()
        return Response({"city": city_serializer.data},
                        status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        if not pk:
            return Response({"error": "Method delete is not allowed!"}, status.HTTP_405_METHOD_NOT_ALLOWED)
        try:
            city = City.objects.get(pk=pk)
        except:
            return Response({"error": "Such city does not exist to delete!"}, status.HTTP_404_NOT_FOUND)
        subscriptions = Subscription.objects.filter(city=city, user=request.user)

        for s in subscriptions:
            WeatherTask(s).delete_city_weather_task()
            SubscriptionTask(s).delete_task()
            s.delete()
        city.delete()
        return Response({"city": "delete city " + str(pk)}, status=status.HTTP_204_NO_CONTENT)


class GetWeather(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        weather = Weather.objects.all()
        return Response({'weather_in_DB': WeatherSerializer(weather, many=True).data}, status=status.HTTP_200_OK)



