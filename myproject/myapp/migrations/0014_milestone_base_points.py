# Generated by Django 5.1.1 on 2024-11-24 13:53

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0013_milestone_point_adjustment"),
    ]

    operations = [
        migrations.AddField(
            model_name="milestone",
            name="base_points",
            field=models.DecimalField(
                decimal_places=2, default=Decimal("0.00"), max_digits=10
            ),
        ),
    ]