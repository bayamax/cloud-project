# Generated by Django 4.2.11 on 2024-06-21 11:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_remove_thread_created_at_alter_threadmessage_sender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='threadmessage',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
