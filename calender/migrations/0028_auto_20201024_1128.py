﻿# Generated by Django 2.1.15 on 2020-10-24 11:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calender', '0027_auto_20200825_1448'),
    ]

    operations = [
        migrations.CreateModel(
            name='Working_Division',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=True, verbose_name='Kích hoạt')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')),
                ('write_date', models.DateTimeField(null=True, verbose_name='Ngày sửa')),
            ],
            options={
                'verbose_name': 'Phân công dự họp',
                'verbose_name_plural': 'Phân công dự họp',
                'default_permissions': (),
            },
        ),
        migrations.AddField(
            model_name='department',
            name='is_vehicle_calender',
            field=models.BooleanField(default=False, verbose_name='Lịch xe'),
        ),
        migrations.AddField(
            model_name='profile',
            name='is_driver',
            field=models.BooleanField(default=False, verbose_name='Lái xe'),
        ),
        migrations.AddField(
            model_name='working_division',
            name='calender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calender.Calender', verbose_name='Lịch'),
        ),
        migrations.AddField(
            model_name='working_division',
            name='create_uid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Người tạo'),
        ),
        migrations.AddField(
            model_name='working_division',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Người được phân công'),
        ),
        migrations.AddField(
            model_name='working_division',
            name='write_uid',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Người sửa'),
        ),
    ]