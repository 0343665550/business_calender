# Generated by Django 2.1.15 on 2020-11-28 09:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calender', '0046_profile_is_driver'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='parent_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='calender.Department', verbose_name='Trực thuộc phòng'),
        ),
    ]
