# Generated by Django 2.1.15 on 2020-06-21 07:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0025_auto_20200619_2212'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calender',
            name='requirements',
        ),
    ]
