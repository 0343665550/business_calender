# Generated by Django 2.1.15 on 2020-05-23 14:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0011_auto_20200523_2129'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calender',
            name='cancel_status',
        ),
    ]