# Generated by Django 2.1.3 on 2019-04-08 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0002_updated_wrong_spell'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='surveydata',
            name='other',
        ),
        migrations.AddField(
            model_name='surveydata',
            name='other_cleaning_technique',
            field=models.CharField(blank=True,
                                   default='',
                                   help_text='If other respondent, explain',
                                   max_length=200,
                                   null=True),
        ),
        migrations.AddField(
            model_name='surveydata',
            name='other_respondent',
            field=models.CharField(blank=True,
                                   default='',
                                   help_text='If other respondent, explain',
                                   max_length=200,
                                   null=True),
        ),
    ]
