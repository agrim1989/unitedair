# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-21 06:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_events_event_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='description',
            field=models.TextField(max_length=2000),
        ),
    ]