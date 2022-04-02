# Generated by Django 2.1.15 on 2020-05-26 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0014_auto_20200524_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calender',
            name='attach_file',
            field=models.FileField(blank=True, null=True, upload_to='files', verbose_name='Đính kèm tệp'),
        ),
        migrations.AlterField(
            model_name='calender',
            name='cancel_status',
            field=models.IntegerField(choices=[(0, 'Bình thường'), (1, 'Hoãn/Huỷ'), (2, 'Đổi thành phần'), (3, 'Đổi thời gian'), (4, 'Bổ sung')], default=0, verbose_name='Trạng thái lịch'),
        ),
        migrations.AlterField(
            model_name='calender',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='Ghi chú'),
        ),
    ]
