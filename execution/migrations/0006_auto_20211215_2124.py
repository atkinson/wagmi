# Generated by Django 3.2.9 on 2021-12-15 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('execution', '0005_alter_fill_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fill',
            name='avgFillPrice',
            field=models.FloatField(default=None, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='fill',
            name='id',
            field=models.BigIntegerField(db_index=True, editable=False, primary_key=True, serialize=False),
        ),
    ]
