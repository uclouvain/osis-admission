# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
# ##############################################################################
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from admission.contrib.models.base import BaseAdmission
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_categories import Categories
from base.models.person import Person


class ContinuingEducationAdmission(BaseAdmission):
    training = models.ForeignKey(
        to="base.EducationGroupYear",
        verbose_name=_("Training"),
        related_name="+",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        choices=ChoixStatutProposition.choices(),
        max_length=30,
        default=ChoixStatutProposition.IN_PROGRESS.name,
    )

    class Meta:
        verbose_name = _("Continuing education admission")
        ordering = ('-created',)
        permissions = []

    def update_detailed_status(self):
        pass


class ContinuingEducationAdmissionManager(models.Manager):
    def get_queryset(self):
        return ContinuingEducationAdmission.objects.all().select_related(
            "candidate__country_of_citizenship",
            "training__academic_year",
            "training__enrollment_campus",
        )


class ContinuingEducationAdmissionProxy(ContinuingEducationAdmission):
    """Proxy model of base.ContinuingEducationAdmission"""

    objects = ContinuingEducationAdmissionManager()

    class Meta:
        proxy = True


@receiver(post_save, sender=EducationGroupYear)
def _invalidate_continuing_education_cache(sender, instance, **kwargs):
    if (  # pragma: no branch
        instance.education_group_type.category == Categories.TRAINING.name
        and instance.education_group_type.name in AnneeInscriptionFormationTranslator.CONTINUING_EDUCATION_TYPES
    ):
        keys = [
            f'admission_permission_{a_uuid}'
            for a_uuid in ContinuingEducationAdmission.objects.filter(training_id=instance.pk).values_list(
                'uuid',
                flat=True,
            )
        ]
        if keys:
            cache.delete_many(keys)


@receiver(post_save, sender=Person)
def _invalidate_candidate_cache(sender, instance, **kwargs):
    keys = [
        f'admission_permission_{a_uuid}'
        for a_uuid in ContinuingEducationAdmission.objects.filter(candidate_id=instance.pk).values_list(
            'uuid',
            flat=True,
        )
    ]
    if keys:
        cache.delete_many(keys)
