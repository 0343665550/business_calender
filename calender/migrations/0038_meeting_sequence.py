# Generated by Django 2.1.15 on 2020-07-16 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0037_auto_20200716_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='sequence',
            field=models.IntegerField(default=0, verbose_name='Thứ tự'),
        ),
    ]
