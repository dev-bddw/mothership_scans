# Generated manually (Django not installed locally to autogenerate) on 2026-08-26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0011_scan_notes_destination_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='destination',
            field=models.TextField(blank=True, null=True),
        ),
    ]
