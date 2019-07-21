# Generated by Django 2.0.13 on 2019-07-17 23:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20190707_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paprikaaccount',
            name='password',
            field=models.CharField(help_text='Password to login to Paprika Cloud Sync', max_length=128, verbose_name='Paprika Cloud Sync Password'),
        ),
        migrations.AlterField(
            model_name='paprikaaccount',
            name='username',
            field=models.CharField(help_text='Email to login to Paprika Cloud Sync', max_length=150, unique=True, verbose_name='Paprika Cloud Sync Email'),
        ),
    ]