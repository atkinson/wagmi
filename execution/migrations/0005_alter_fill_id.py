# Generated by Django 3.2.9 on 2021-12-15 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execution', '0004_fill_future'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fill',
            name='id',
            field=models.BigIntegerField(editable=False, primary_key=True, serialize=False),
        ),
    ]
