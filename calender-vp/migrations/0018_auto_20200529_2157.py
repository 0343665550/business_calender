# Generated by Django 2.1.15 on 2020-05-29 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0017_merge_20200529_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='calender',
            name='check_calender',
            field=models.BooleanField(default=False, verbose_name='Trạng thái duyệt'),
        ),
        migrations.AlterField(
            model_name='department',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='Ghi chú'),
        ),
    ]
