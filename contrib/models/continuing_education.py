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
from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.contrib.models.base import BaseAdmission, BaseAdmissionQuerySet
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition


class ContinuingEducationAdmission(BaseAdmission):
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


class ContinuingEducationAdmissionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "candidate__country_of_citizenship",
                "training__academic_year",
            )
            .annotate_campus()
        )


class ContinuingEducationAdmissionProxy(ContinuingEducationAdmission):
    """Proxy model of base.ContinuingEducationAdmission"""

    objects = ContinuingEducationAdmissionManager()

    class Meta:
        proxy = True
