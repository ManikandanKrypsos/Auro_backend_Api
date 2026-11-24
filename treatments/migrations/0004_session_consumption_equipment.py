"""
Usage is now confirmed by the therapist per session (SessionConsumption + its lines) instead of being
deducted automatically on completion; treatments can require a machine (rooms.Equipment).
The old auto-deduction rows are replaced (their stock movements stay in the ledger).
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("appointments", "0003_alter_appointment_status"),
        ("inventory", "0007_drop_platform_wide_unique"),
        ("rooms", "0004_equipment"),
        ("treatments", "0003_consumables"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(name="AppointmentConsumption"),
        migrations.AddField(
            model_name="treatment",
            name="equipment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="treatments",
                to="rooms.equipment",
            ),
        ),
        migrations.CreateModel(
            name="SessionConsumption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=255)),
                ("reversed", models.BooleanField(default=False)),
                ("reversed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "appointment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="consumption_records",
                        to="appointments.appointment",
                    ),
                ),
                (
                    "confirmed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="AppointmentConsumption",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("planned", models.PositiveIntegerField(default=0)),
                ("quantity", models.PositiveIntegerField()),
                ("deducted", models.PositiveIntegerField(default=0)),
                ("shortfall", models.PositiveIntegerField(default=0)),
                (
                    "unit_cost",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="inventory.inventoryitem",
                    ),
                ),
                (
                    "lot",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="inventory.lot",
                    ),
                ),
                (
                    "movement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="inventory.stockmovement",
                    ),
                ),
                (
                    "record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="treatments.sessionconsumption",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
