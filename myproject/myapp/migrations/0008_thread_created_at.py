# Generated by Django 4.2.11 on 2024-06-21 14:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_alter_threadmessage_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]