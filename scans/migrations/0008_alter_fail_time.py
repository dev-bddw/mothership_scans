# Generated by Django 3.2.12 on 2023-01-11 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0007_auto_20230110_0833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fail',
            name='time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
