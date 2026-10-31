from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.students.models import Student


class Package(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="packages",
        verbose_name="alumna",
    )
    original_quantity = models.PositiveIntegerField(
        "cantidad original",
        default=10,
        validators=[MinValueValidator(1)],
    )
    remaining_quantity = models.PositiveIntegerField(
        "cantidad restante",
        editable=False,
    )
    created_at = models.DateTimeField("fecha de creación", auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_packages",
        verbose_name="administradora responsable",
    )

    class Meta:
        ordering = ("created_at", "id")
        verbose_name = "paquete"
        verbose_name_plural = "paquetes"
        constraints = [
            models.CheckConstraint(
                condition=Q(original_quantity__gt=0),
                name="package_original_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(remaining_quantity__gte=0),
                name="package_remaining_quantity_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(remaining_quantity__lte=F("original_quantity")),
                name="package_remaining_not_above_original",
            ),
        ]

    def __str__(self):
        return f"Paquete #{self.pk} · {self.student}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.remaining_quantity = self.original_quantity
        super().save(*args, **kwargs)
