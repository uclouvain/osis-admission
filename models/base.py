import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.models import AdmissionType


class BaseAdmission(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    type = models.CharField(
        verbose_name=_("admission_type"),
        max_length=255,
        choices=AdmissionType.choices(),
        db_index=True,
    )
    candidate = models.ForeignKey(
        to="base.Person",
        verbose_name=_("admission_candidate"),
        related_name="admissions_candidate",
        on_delete=models.CASCADE,
    )
    comment = models.TextField(verbose_name=_("admission_comment"))
    author = models.ForeignKey(
        to='base.Person',
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    created = models.DateField(
        verbose_name=_('created'), auto_now_add=True, editable=False
    )
    modified = models.DateField(
        verbose_name=_('modified'), auto_now=True, editable=False
    )

    class Meta:
        abstract = True
        ordering = ('-created',)
