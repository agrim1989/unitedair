# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-21 05:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20181121_0529'),
    ]

    operations = [
        migrations.AddField(
            model_name='events',
            name='event_image',
            field=models.URLField(default=1),
            preserve_default=False,
        ),
    ]
