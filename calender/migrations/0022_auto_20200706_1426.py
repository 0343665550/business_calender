﻿# Generated by Django 2.1.15 on 2020-07-06 14:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0021_auto_20200702_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='calender',
            name='other_prepare',
            field=models.TextField(blank=True, null=True, verbose_name='Đơn vị chuẩn bị khác'),
        ),
        migrations.AddField(
            model_name='calender',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Địa điểm khác'),
        ),
    ]
