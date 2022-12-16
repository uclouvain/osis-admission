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
from contextlib import suppress

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import api_settings

from admission.contrib.models.base import BaseAdmission, BaseAdmissionQuerySet, admission_directory_path
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
from base.models.academic_year import AcademicYear
from osis_common.ddd.interface import BusinessException
from osis_document.contrib import FileField


class ContinuingEducationAdmission(BaseAdmission):
    status = models.CharField(
        choices=ChoixStatutProposition.choices(),
        max_length=30,
        default=ChoixStatutProposition.IN_PROGRESS.name,
    )

    diploma_equivalence = FileField(
        blank=True,
        mimetypes=['application/pdf'],
        upload_to=admission_directory_path,
        verbose_name=_('Diploma equivalence'),
    )

    class Meta:
        verbose_name = _("Continuing education admission")
        ordering = ('-created',)
        permissions = []

    def update_detailed_status(self):
        from admission.ddd.admission.formation_continue.commands import (
            VerifierPropositionQuery,
            DeterminerAnneeAcademiqueEtPotQuery,
        )
        from admission.utils import gather_business_exceptions
        from infrastructure.messages_bus import message_bus_instance

        error_key = api_settings.NON_FIELD_ERRORS_KEY
        self.detailed_status = gather_business_exceptions(VerifierPropositionQuery(self.uuid)).get(error_key, [])

        with suppress(BusinessException):
            dto: 'InfosDetermineesDTO' = message_bus_instance.invoke(DeterminerAnneeAcademiqueEtPotQuery(self.uuid))
            self.determined_academic_year = AcademicYear.objects.get(year=dto.annee)
            self.determined_pool = dto.pool.name
        self.save(update_fields=['detailed_status', 'determined_academic_year', 'determined_pool'])


class ContinuingEducationAdmissionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "candidate__country_of_citizenship",
                "training__academic_year",
                "training__education_group_type",
                "training__main_domain",
                "determined_academic_year",
            )
            .annotate_campus()
            .annotate_pool_end_date()
        )


class ContinuingEducationAdmissionProxy(ContinuingEducationAdmission):
    """Proxy model of base.ContinuingEducationAdmission"""

    objects = ContinuingEducationAdmissionManager()

    class Meta:
        proxy = True
