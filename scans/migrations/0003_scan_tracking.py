# Generated by Django 3.2.12 on 2022-07-25 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0002_scan_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='tracking',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
