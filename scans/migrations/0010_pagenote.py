# Generated by Django 3.2.12 on 2023-02-01 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0009_auto_20230118_1342'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, max_length=10000, null=True)),
                ('page', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]
