FROM python:3.10
RUN apt-get update -y \
     && apt-get install -y netcat
RUN apt-get upgrade -y \
    && apt-get install -y postgresql gcc python3-dev musl-dev


ENV PYTHONDONTWRITEBITECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/app

#COPY ./entrypoint.sh /usr/src/app/entrypoint.sh
#ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

EXPOSE 8000
#CMD ["python", "manage.py", "migrate"]
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]