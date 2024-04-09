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
from django.db import models
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist

__all__ = [
    'CategorizedFreeDocument',
    'TOKEN_ACADEMIC_YEAR',
]

# Tokens that will be replaced in the long label
TOKEN_ACADEMIC_YEAR = '{annee_academique}'


class CategorizedFreeDocument(models.Model):
    checklist_tab = models.CharField(
        choices=OngletsChecklist.choices(),
        max_length=255,
        default='',
        blank=True,
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
