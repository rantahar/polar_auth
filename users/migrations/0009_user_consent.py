# Generated by Django 3.2 on 2021-06-01 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20210601_1129'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='consent',
            field=models.BooleanField(default=False, verbose_name='consent'),
            preserve_default=False,
        ),
    ]
