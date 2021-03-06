# Generated by Django 2.0.13 on 2019-08-18 20:05

from django.db import migrations


TYPE_RECIPE_EDITED = 'recipe_edited'
FIELDS_TO_DIFF = {'photo_hash', 'name', 'ingredients', 'source', 'total_time', 'cook_time', 'prep_time', 'description', 'source_url', 'difficulty', 'directions', 'notes', 'nutritional_info', 'servings', 'rating', 'categories'}


def forwards(apps, schema_editor):
    'Delete EDITED NewsItems where fields_changed is empty or hash'
    NewsItem = apps.get_model("core", "NewsItem")

    for ni in NewsItem.objects.filter(type=TYPE_RECIPE_EDITED):
        fields = ni.payload['fields_changed']
        ignored_fields = set(fields) - FIELDS_TO_DIFF
        if not fields:
            print(f'Deleting NewsItem {ni.id}: {fields}')
            ni.delete()
        elif ignored_fields:
            for f in ignored_fields:
                ni.payload['fields_changed'].remove(f)
            if ni.payload['fields_changed']:
                print(f'Saving NewsItem {ni.id}: {ni.payload["fields_changed"]}')
                ni.save()
            else:
                print(f'Deleting NewsItem {ni.id}: {fields}')
                ni.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_split_rating_from_edit_newsitems'),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
