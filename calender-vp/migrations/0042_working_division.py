# Generated by Django 2.1.15 on 2020-10-14 23:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calender', '0041_department_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='Working_Division',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')),
                ('write_date', models.DateTimeField(auto_now=True, null=True, verbose_name='Ngày sửa')),
                ('calender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calender.Calender', verbose_name='Lịch')),
                ('create_uid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Người tạo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Người được phân công')),
                ('write_uid', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Người sửa')),
            ],
            options={
                'verbose_name': 'Phân công dự họp',
                'verbose_name_plural': 'Phân công dự họp',
            },
        ),
    ]