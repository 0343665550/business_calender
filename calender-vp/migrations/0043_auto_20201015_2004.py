# Generated by Django 2.1.15 on 2020-10-15 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0042_working_division'),
    ]

    operations = [
        migrations.AddField(
            model_name='working_division',
            name='active',
            field=models.BooleanField(default=True, verbose_name='Kích hoạt'),
        ),
        migrations.AlterField(
            model_name='working_division',
            name='write_date',
            field=models.DateTimeField(null=True, verbose_name='Ngày sửa'),
        ),
    ]
