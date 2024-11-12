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
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.constants import CONTEXT_GENERAL, CONTEXT_CONTINUING, CONTEXT_DOCTORATE
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist as OngletsChecklistDoctorat,
)
from admission.ddd.admission.formation_continue.domain.model.enums import OngletsChecklist as OngletsChecklistContinue
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist as OngletsChecklistGenerale

__all__ = [
    'CategorizedFreeDocument',
    'TOKEN_ACADEMIC_YEAR',
]

# Tokens that will be replaced in the long label
TOKEN_ACADEMIC_YEAR = '{annee_academique}'


class CategorizedFreeDocument(models.Model):
    checklist_tab = models.CharField(
        choices=[
            (
                pgettext_lazy('admission context', 'General education'),
                OngletsChecklistGenerale.choices(),
            ),
            (
                pgettext_lazy('admission context', 'Continuing education'),
                OngletsChecklistContinue.choices(),
            ),
            (
                pgettext_lazy('admission context', 'Doctorate education'),
                OngletsChecklistDoctorat.choices(),
            ),
        ],
        max_length=255,
        default='',
        blank=True,
        verbose_name=_('Checklist tab'),
    )

    admission_context = models.CharField(
        choices=(
            (CONTEXT_GENERAL, pgettext_lazy('admission context', 'General education')),
            (CONTEXT_CONTINUING, pgettext_lazy('admission context', 'Continuing education')),
            (CONTEXT_DOCTORATE, pgettext_lazy('admission context', 'Doctorate education')),
        ),
        max_length=20,
        default='',
        verbose_name=_('Admission context'),
    )

    short_label_fr = models.CharField(
        max_length=255,
        verbose_name=_('Short label in french'),
    )

    short_label_en = models.CharField(
        max_length=255,
        verbose_name=_('Short label in english'),
        default='',
        blank=True,
    )

    long_label_fr = models.TextField(
        verbose_name=_('Long label in french'),
    )

    long_label_en = models.TextField(
        blank=True,
        verbose_name=_('Long label in english'),
    )

    with_academic_year = models.BooleanField(
        default=False,
        verbose_name=_('With academic year'),
    )

    def __str__(self):
        return self.short_label_fr

    def clean(self):
        result = super().clean()

        # Check that the checklist tab is valid for the admission context
        if (
            self.admission_context
            and self.checklist_tab
            and not hasattr(
                {
                    CONTEXT_GENERAL: OngletsChecklistGenerale,
                    CONTEXT_CONTINUING: OngletsChecklistContinue,
                    CONTEXT_DOCTORATE: OngletsChecklistDoctorat,
                }[self.admission_context],
                self.checklist_tab,
            )
        ):
            raise ValidationError(_('The checklist tab is not valid for this admission context.'))

        return result
