# Generated by Django 3.2.9 on 2021-11-14 14:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_id', models.CharField(max_length=100)),
                ('available_balance', models.FloatField()),
                ('current_balance', models.FloatField()),
                ('name', models.CharField(max_length=100)),
                ('account_type', models.CharField(max_length=100)),
                ('account_subtype', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_id', models.CharField(max_length=100)),
                ('access_token', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100)),
                ('amount', models.FloatField()),
                ('date', models.DateField()),
                ('name', models.CharField(max_length=100)),
                ('payment_channel', models.CharField(max_length=100)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plaidIntegration.account')),
            ],
        ),
        migrations.CreateModel(
            name='ItemMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('webhook', models.CharField(max_length=100)),
                ('update_type', models.CharField(max_length=100)),
                ('item_meta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plaidIntegration.item')),
            ],
        ),
        migrations.AddField(
            model_name='account',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plaidIntegration.item'),
        ),
    ]