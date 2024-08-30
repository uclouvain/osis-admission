# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from ordered_model.models import OrderedModel

from admission.contrib.models.form_item import TranslatedJSONField
from admission.ddd.admission.doctorat.preparation.domain.model.enums import ChoixStatutPropositionDoctorale
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION
from admission.ddd.admission.enums.type_demande import TypeDemande


class CommonWorkingList(OrderedModel):
    name = TranslatedJSONField(
        verbose_name=_('Name of the working list'),
    )

    checklist_filters_mode = models.CharField(
        choices=ModeFiltrageChecklist.choices(),
        verbose_name=_('Checklist filters mode'),
        max_length=16,
        default='',
        blank=True,
    )

    checklist_filters = models.JSONField(
        default=dict,
        verbose_name=_('Checklist filters'),
        blank=True,
    )

    admission_type = models.CharField(
        blank=True,
        verbose_name=_('Admission type'),
        choices=TypeDemande.choices(),
        default='',
        max_length=16,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name.get(settings.LANGUAGE_CODE)


class WorkingList(CommonWorkingList):
    quarantine = models.BooleanField(null=True)

    admission_statuses = ArrayField(
        default=list,
        verbose_name=_('Admission statuses'),
        base_field=models.CharField(
            choices=CHOIX_STATUT_TOUTE_PROPOSITION,
            max_length=30,
        ),
        blank=True,
    )

    class Meta(OrderedModel.Meta):
        verbose_name = _('Working list')
        verbose_name_plural = _('Working lists')


class DoctorateWorkingList(CommonWorkingList):
    admission_statuses = ArrayField(
        default=list,
        verbose_name=_('Admission statuses'),
        base_field=models.CharField(
            choices=ChoixStatutPropositionDoctorale.choices(),
            max_length=30,
        ),
        blank=True,
    )

    class Meta(OrderedModel.Meta):
        verbose_name = _('Doctorate working list')
        verbose_name_plural = _('Doctorate working lists')
