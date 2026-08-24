# Generated manually (Django not installed locally to autogenerate) on 2026-08-24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0010_pagenote'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scan',
            name='destination_type',
            field=models.CharField(
                blank=True,
                null=True,
                max_length=20,
                choices=[('internal', 'Internal'), ('external', 'External')],
            ),
        ),
    ]
