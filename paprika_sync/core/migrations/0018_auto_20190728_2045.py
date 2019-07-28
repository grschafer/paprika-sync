# Generated by Django 2.0.13 on 2019-07-28 20:45
import hashlib

from django.db import migrations, models


FIELDS_TO_DIFF = ['photo_hash', 'name', 'ingredients', 'source', 'total_time', 'cook_time', 'prep_time', 'description', 'source_url', 'difficulty', 'directions', 'notes', 'nutritional_info', 'servings', 'rating', 'categories']


def compute_import_stable_hash(Recipe, recipe):
    'Hash that is stable, even if a recipe is imported from another account'
    hash = hashlib.sha1()
    for field in sorted(Recipe._meta.get_fields(), key=lambda f: f.name):
        if field.name in FIELDS_TO_DIFF:
            if field.one_to_many or field.many_to_many:
                value_list = getattr(recipe, field.name).values_list('name', flat=True)
                value = ','.join(value_list)
                add = value.encode()
                hash.update(add)
            else:
                value = getattr(recipe, field.name)
                add = str(value).encode()
                hash.update(add)
    return hash.hexdigest()


def forwards(apps, schema_editor):
    'Update import_stable_hash for all recipes'
    Recipe = apps.get_model("core", "Recipe")

    for r in Recipe.objects.all():
        r.import_stable_hash = compute_import_stable_hash(Recipe, r)
        r.save()


def backwards(apps, schema_editor):
    'Update import_stable_hash for all recipes'
    Recipe = apps.get_model("core", "Recipe")

    for r in Recipe.objects.all():
        r.import_stable_hash = ''
        r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20190717_2322'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name'], 'verbose_name_plural': 'categories'},
        ),
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ['-id']},
        ),
        migrations.AddField(
            model_name='recipe',
            name='import_stable_hash',
            field=models.CharField(blank=True, help_text='Hash of recipe data that is stable, even if a recipe is imported from another account', max_length=200),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(db_index=True, max_length=1000),
        ),
        migrations.RunPython(forwards, backwards),
    ]
