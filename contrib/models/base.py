import uuid

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseAdmission(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    candidate = models.ForeignKey(
        to="base.Person",
        verbose_name=_("Candidate"),
        related_name="%(class)ss",
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

    professional_valuated_experiences = models.ManyToManyField(
        'osis_profile.ProfessionalExperience',
        related_name='valuated_from_%(class)s',
        verbose_name=_('The professional experiences that have been valuated from this admission.'),
    )
    educational_valuated_experiences = models.ManyToManyField(
        'osis_profile.EducationalExperience',
        related_name='valuated_from_%(class)s',
        verbose_name=_('The educational experiences that have been valuated from this admission.'),
    )
    detailed_status = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete('admission_permission_{}'.format(self.uuid))

    class Meta:
        abstract = True


def admission_directory_path(admission: BaseAdmission, filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/{}'.format(
        admission.candidate.uuid,
        admission.uuid,
        filename,
    )
