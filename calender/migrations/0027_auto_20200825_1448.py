﻿# Generated by Django 2.1.15 on 2020-08-25 14:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0026_auto_20200801_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Kích hoạt'),
        ),
    ]