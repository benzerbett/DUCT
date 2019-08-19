# Generated by Django 2.1.3 on 2019-04-09 12:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '0013_added_post_code'),
        ('indicator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='country',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='geodata.Country'),
        ),
    ]
