import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from osis_profile.models import Experience
from .enums.admission_type import AdmissionType


class BaseAdmission(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    type = models.CharField(
        verbose_name=_("Type"),
        max_length=255,
        choices=AdmissionType.choices(),
        db_index=True,
        default=AdmissionType.ADMISSION.name,
    )
    candidate = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Candidate"),
        related_name="admissions",
        on_delete=models.PROTECT,
        editable=False,
    )
    comment = models.TextField(
        default='',
        verbose_name=_("Comment"),
        blank=True,
    )

    created = models.DateTimeField(verbose_name=_('Created'), auto_now_add=True)
    modified = models.DateTimeField(verbose_name=_('Modified'), auto_now=True)

    valuated_experiences = models.ManyToManyField(
        Experience,
        related_name='valuated_from',
        verbose_name=_('The experiences that have been valuated from this admission.'),
    )

    class Meta:
        abstract = True


def admission_directory_path(admission: BaseAdmission, filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/{}'.format(
        admission.candidate.uuid,
        admission.uuid,
        filename,
    )
