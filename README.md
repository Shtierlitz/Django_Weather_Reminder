# DjangoWeatherReminder

## Description
This project is designed as a weather service with the ability to subscribe to the weather 
from different cities with different frequency and receive it by email.

## Technologies used
`Django`, `Django Rest Framework`, `Celery`, `Docker`, `weather api services`, `PostgreSQL`, `Nginx`



## Getting started

To make it easy for you to get started with Django Weather Reminder, 
here's a list of recommended next steps.


## Download
Download the repository with this command: 
```bash
git clone https://github.com/Shtierlitz/Django_Weather_Reminder.git
```

##Create Files
For the local server to work correctly, create your own file `local_settings.py` 
and place it in a folder next to the file `settings.py` of this Django project.
You will also need to create `.env` file and place it in the root of the project.

### Required contents of the local_settings.py file:
```python  
import os  
from pathlib import Path  
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'static')  
REDIS_HOST = '6379'  
REDIS_PORT = '127.0.0.1' 

CELERY_BROKER_URL = f'redis://{REDIS_PORT}:{REDIS_HOST}/0'  
CELERY_RESULT_BACKEND = f'redis://{REDIS_PORT}:{REDIS_HOST}/0'  
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}  
CELERY_ACCEPT_CONTENT = ['application/json']  
CELERY_TASK_SERIALIZER = 'json' 
CELERY_RESULT_SERIALIZER = 'json'  
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'  
CELERY_IMPORTS = [
    'weatherreminder.tasks',
]  
```

### Required contents of the .env file:
```python
WEATHER_API_KEY='<your OpenWeatherMap token>'  
WEATHER_BIT_KEY='<your WeatherBit token>'  
SECRET_KEY='<your SECRET key>'   

EMAIL_HOST_USER="<your email>"  
EMAIL_HOST_PASSWORD="<your google app password>"  
DEFAULT_FROM_EMAIL="<your email>"  
RECIPIENTS_EMAIL="<your email>"  

DATABASE_NAME="<database name>"  
DATABASE_USER="<database username>"  
DATABASE_PASS="<database password>"  
DATABASE_HOST="pg_db"  
DATABASE_PORT="5432"  

USER_PASS="<database user password>"
```

# Localhost development

## Django run
To run localhost server just get to the folder where `manage.py` is and then run the command:
```bash
python manage.py runserver
```

## Redis cli run on Windows
Install Linux on Windows with WSL https://learn.microsoft.com/en-us/windows/wsl/install  
Install and run Redis cli https://redis.io/docs/getting-started/installation/install-redis-on-windows/
```bash 
sudo service redis-server start  
redis-cli
```

# Celery 
###Celery Worker run on Windows
Run in new terminal:
```bash
pip install eventlet  
celery -A djangoweatherreminder worker -l info -P eventlet
```

###Celery beat
Run in new terminal:
```bash
celery -A djangoweatherreminder beat -l info 
```

### Celery Flower
Run in new terminal:
```bash
celery -A djangoweatherreminder flower  --address=127.0.0.1 --port=5566
```
## Test 

To run tests from the localhost, type in the folder next to the file `manage.py`:  
```bash
python manage.py test weatherreminder.tests
````

## Docker localhost
To use docker in localhost you need to have `local_settings.py` behind yours `settings.py` file.
```bash
run docker-compose up --build
````

## Docker deploy
To use docker to deploy project on server you need to delete `local_settings.py`.  
Find server and create an instance.  
Run next commands:  
```bash
sudo apt-get update  
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common  
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -  
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"  
sudo apt-get update  
sudo apt-get install docker-ce  
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)"  
sudo chmod +x /usr/local/bin/docker-compose  
docker --version  
```

###Now clone repository:
```bash
sudo git clone https://github.com/Shtierlitz/Django_Weather_Reminder.git  
```

### Dont forget to create .env file
### Now you can run Docker container in your server machine:
```bash
sudo docker-compose -f docker-compose.prod.yml up -d --build
```

##Api 
To get excess to `API` if you want to use `Postman` 
you need to generate and verify `token`. It is possible after you register in website

`../api/v1/token/` - obtain token  
`../api/v1/token/verify/` - verify your token  
`../api/v1/token/refresh/` - refresh token if it has expired

### You can follow the following paths to use the `API`:

`../api/v1/subscriptions/` - get users subscriptions list  
`../api/v1/subscriptions/pk/` - get or delete users subscription  
`../api/v1/cities/` - get users city list  
`../api/v1/cities/pk/` - get or delete city  
`../api/v1/get_weather/` - get list of all existing weathers in database

#Sources
 Django Rest Framework https://www.django-rest-framework.org/  
 Celery https://docs.celeryq.dev/en/stable/getting-started/introduction.html  
 Docker https://docs.docker.com/  
 Redis https://redis.io/docs/getting-started/installation/install-redis-on-windows/  
 DjangoSchool https://www.youtube.com/@DjangoSchool