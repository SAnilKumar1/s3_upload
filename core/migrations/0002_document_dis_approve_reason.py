# Generated by Django 3.2.13 on 2022-07-12 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='dis_approve_reason',
            field=models.CharField(default='', max_length=250),
        ),
    ]