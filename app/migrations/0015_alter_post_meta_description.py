# Generated by Django 5.1.4 on 2025-05-24 09:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_post_meta_description_post_meta_keywords_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='meta_description',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
