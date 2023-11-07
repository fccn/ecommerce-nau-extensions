# Generated by Django 3.2.16 on 2023-10-10 13:23

import django.db.models.deletion
import jsonfield.encoder
import jsonfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('basket', '0014_line_date_updated'),
        ('nau_extensions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basketbillinginformation',
            options={'verbose_name': 'Basket Billing Information', 'verbose_name_plural': 'Basket Billing Informations'},
        ),
        migrations.AlterField(
            model_name='basketbillinginformation',
            name='vatin',
            field=models.CharField(blank=True, help_text='The value-added tax identification number or VAT identification number can be used to identify a business or a taxable person in the European Union.', max_length=255, verbose_name='VAT Identification Number (VATIN)'),
        ),
        migrations.CreateModel(
            name='BasketTransactionIntegration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('To be sent', 'To be sent'), ('Sent with success', 'Sent with success'), ('Sent with error', 'Sent with error')], default='To be sent', max_length=255)),
                ('request', jsonfield.fields.JSONField(dump_kwargs={'cls': jsonfield.encoder.JSONEncoder, 'separators': (',', ':')}, load_kwargs={})),
                ('response', jsonfield.fields.JSONField(dump_kwargs={'cls': jsonfield.encoder.JSONEncoder, 'separators': (',', ':')}, load_kwargs={})),
                ('basket', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='basket_transaction_integration', to='basket.basket')),
            ],
        ),
    ]
