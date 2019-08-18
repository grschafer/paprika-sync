# Generated by Django 2.0.13 on 2019-08-18 21:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_delete_noop_edited_newsitems'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsitem',
            name='previous_recipe',
            field=models.ForeignKey(blank=True, help_text='Previous version of the recipe', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Recipe'),
        ),
        migrations.AddField(
            model_name='newsitem',
            name='recipe',
            field=models.ForeignKey(blank=True, help_text='Related recipe (e.g. if type is added, edited, rated, deleted)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='core.Recipe'),
        ),
    ]