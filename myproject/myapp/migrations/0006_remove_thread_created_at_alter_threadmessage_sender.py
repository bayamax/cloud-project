# Generated by Django 4.2.11 on 2024-06-21 10:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_thread_threadmessage_delete_generalmessage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='thread',
            name='created_at',
        ),
        migrations.AlterField(
            model_name='threadmessage',
            name='sender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
