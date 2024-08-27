# Generated by Django 4.1.13 on 2024-08-27 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CalculationIDs',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('context_id', models.TextField(default='test_id')),
                ('calculation_record', models.TextField()),
                ('calculation_id', models.TextField(default='test_id')),
            ],
        ),
        migrations.CreateModel(
            name='CalculationLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('trigger_name', models.TextField(null=True)),
                ('message_type', models.TextField(default='')),
                ('calculationId', models.TextField(default='test_id')),
                ('calculation_record', models.TextField(default='legacy')),
                ('message', models.TextField()),
                ('method', models.TextField()),
                ('is_notification', models.BooleanField(default=False)),
            ],
        ),
    ]