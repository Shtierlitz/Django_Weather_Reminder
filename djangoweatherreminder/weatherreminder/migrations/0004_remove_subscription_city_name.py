# Generated by Django 4.1.7 on 2023-03-11 13:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weatherreminder', '0003_subscription_city_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='city_name',
        ),
    ]