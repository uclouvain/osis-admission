import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums.admission_type import AdmissionType


class BaseAdmission(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    type = models.CharField(
        verbose_name=_("Type"),
        max_length=255,
        choices=AdmissionType.choices(),
        db_index=True,
    )
    candidate = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Candidate"),
        related_name="admissions",
        on_delete=models.CASCADE,
    )
    comment = models.TextField(verbose_name=_("Comment"))
    author = models.ForeignKey(
        to='base.Person',
        verbose_name=_('Author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    created = models.DateTimeField(verbose_name=_('Created'), auto_now_add=True)
    modified = models.DateTimeField(verbose_name=_('Modified'), auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return _("{degree} [{type}] for {candidate}").format(
            degree=self._meta.verbose_name,
            type=self.get_type_display(),
            candidate=self.candidate,
        )
