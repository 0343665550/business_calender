# Generated by Django 2.1.15 on 2020-07-16 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0035_auto_20200716_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calender',
            name='create_depart_id',
            field=models.IntegerField(default=1, verbose_name='Phòng tạo'),
        ),
    ]