# Generated by Django 3.2.7 on 2021-10-31 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmanager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='image',
            field=models.ImageField(blank=True, upload_to='book_images'),
        ),
    ]
