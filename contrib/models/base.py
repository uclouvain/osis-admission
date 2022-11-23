import uuid

from django.contrib.postgres.aggregates import StringAgg
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import OuterRef, Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileField

from admission.contrib.models.form_item import ConfigurableModelFormItemField
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.models.person import Person
from program_management.models.education_group_version import EducationGroupVersion


def admission_directory_path(admission: 'BaseAdmission', filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/{}'.format(
        admission.candidate.uuid,
        admission.uuid,
        filename,
    )


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
        related_name='valuated_from_admission',
        verbose_name=_('The professional experiences that have been valuated from this admission.'),
    )
    educational_valuated_experiences = models.ManyToManyField(
        'osis_profile.EducationalExperience',
        related_name='valuated_from_admission',
        verbose_name=_('The educational experiences that have been valuated from this admission.'),
    )
    detailed_status = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    training = models.ForeignKey(
        to="base.EducationGroupYear",
        verbose_name=_("Training"),
        related_name="+",
        on_delete=models.CASCADE,
    )

    specific_question_answers = ConfigurableModelFormItemField(
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
        upload_to=admission_directory_path,
        education_field_name='training',
    )

    curriculum = FileField(
        blank=True,
        mimetypes=['application/pdf'],
        upload_to=admission_directory_path,
        verbose_name=_('Curriculum'),
    )

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete('admission_permission_{}'.format(self.uuid))


@receiver(post_save, sender=EducationGroupYear)
def _invalidate_doctorate_cache(sender, instance, **kwargs):
    admission_types = AnneeInscriptionFormationTranslator.ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.keys()
    if (
        instance.education_group_type.category == Categories.TRAINING.name
        and instance.education_group_type.name in admission_types
    ):  # pragma: no branch
        keys = [
            f'admission_permission_{a_uuid}'
            for a_uuid in BaseAdmission.objects.filter(training_id=instance.pk).values_list('uuid', flat=True)
        ]
        if keys:
            cache.delete_many(keys)


@receiver(post_save, sender=Person)
def _invalidate_candidate_cache(sender, instance, **kwargs):
    keys = [
        f'admission_permission_{a_uuid}'
        for a_uuid in BaseAdmission.objects.filter(candidate_id=instance.pk).values_list('uuid', flat=True)
    ]
    if keys:
        cache.delete_many(keys)


class BaseAdmissionQuerySet(models.QuerySet):
    def annotate_campus(self):
        return self.annotate(
            teaching_campus=Subquery(
                EducationGroupVersion.objects.filter(offer_id=OuterRef('training_id'))
                .select_related('root_group__main_teaching_campus')
                .annotate(
                    campus_name=StringAgg(
                        'root_group__main_teaching_campus__name',
                        delimiter=',',
                        distinct=True,
                    )
                )
                .values('campus_name')[:1]
            )
        )
