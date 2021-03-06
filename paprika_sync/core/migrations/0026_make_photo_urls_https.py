# Generated by Django 2.0.13 on 2019-08-18 22:47

from django.db import migrations

from paprika_sync.core.utils import make_s3_url_https


def forwards(apps, schema_editor):
    'Convert http photo urls to https ones'
    Recipe = apps.get_model("core", "Recipe")

    for r in Recipe.objects.exclude(photo_url=''):
        r.photo_url = make_s3_url_https(r.photo_url)
        r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_backfill_newsitem_recipe_relations'),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
