# Generated by Django 5.0.4 on 2024-07-25 04:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('score_management', '0003_alter_userscore_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userscore',
            name='status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='score_management.statussetting'),
        ),
    ]
