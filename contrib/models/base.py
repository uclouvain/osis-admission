##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import uuid

from django.contrib.postgres.aggregates import StringAgg
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import OuterRef, Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
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
        blank=True,
        related_name='valuated_from_admission',
        verbose_name=_('The professional experiences that have been valuated from this admission.'),
    )
    educational_valuated_experiences = models.ManyToManyField(
        'osis_profile.EducationalExperience',
        blank=True,
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
    determined_academic_year = models.ForeignKey(
        to="base.AcademicYear",
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    determined_pool = models.CharField(
        choices=AcademicCalendarTypes.choices(),
        max_length=70,
        null=True,
        blank=True,
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
    valuated_secondary_studies_person = models.OneToOneField(
        to='base.Person',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_('The person whose the secondary studies have been valuated by this admission'),
    )

    confirmation_elements = models.JSONField(
        blank=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    # Only the candidate can be valuated
                    valuated_secondary_studies_person_id=models.F("candidate_id"),
                ),
                name='only_candidate_can_be_valuated',
            ),
        ]

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
            ),
        )

    def annotate_pool_end_date(self):
        today = timezone.now().today()
        return self.annotate(
            pool_end_date=models.Subquery(
                AcademicCalendar.objects.filter(
                    reference=OuterRef('determined_pool'),
                    start_date__lte=today,
                    end_date__gte=today,
                ).values('end_date')[:1],
            ),
        )
