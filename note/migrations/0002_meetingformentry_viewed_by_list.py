# Generated by Django 4.0.4 on 2022-06-01 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('note', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetingformentry',
            name='viewed_by_list',
            field=models.ManyToManyField(related_name='noteViewedBy', to='note.contact'),
        ),
    ]
