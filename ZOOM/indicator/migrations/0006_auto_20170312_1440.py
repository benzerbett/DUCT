# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-12 14:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicator', '0005_auto_20170307_1129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicatorsource',
            name='id',
            field=models.CharField(max_length=500, primary_key=True, serialize=False),
        ),
    ]