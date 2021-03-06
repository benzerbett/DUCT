# Generated by Django 2.1.3 on 2019-01-15 16:38

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '0006_auto_20190110_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='region',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='region',
            name='polygons',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='subnational',
            name='polygons',
            field=django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326),
        ),
    ]
