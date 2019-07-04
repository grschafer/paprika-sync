# Generated by Django 2.0.13 on 2019-06-29 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_category_paprika_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='categories',
            field=models.ManyToManyField(related_name='recipes', to='core.Category'),
        ),
        migrations.AlterField(
            model_name='category',
            name='parent_uid',
            field=models.CharField(blank=True, db_index=True, max_length=200),
        ),
    ]