# Generated by Django 2.1.15 on 2020-07-16 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0033_auto_20200716_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calender',
            name='create_depart_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='calender.Department', verbose_name='Phòng tạo'),
        ),
    ]
