# Generated by Django 3.2.16 on 2023-10-10 14:26

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nau_extensions', '0002_auto_20231010_1323'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='baskettransactionintegration',
            options={'get_latest_by': 'created'},
        ),
        migrations.AddField(
            model_name='baskettransactionintegration',
            name='created',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
