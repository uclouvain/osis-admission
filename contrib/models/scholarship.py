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
import uuid as uuid
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.ddd.admission.enums.type_bourse import TypeBourse


class Scholarship(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
    )

    short_name = models.CharField(
        verbose_name=_('Short name'),
        max_length=50,
    )

    long_name = models.CharField(
        max_length=255,
        verbose_name=_('Long name'),
        blank=True,
        default='',
    )

    deleted = models.BooleanField(
        verbose_name=_('Deleted'),
        default=False,
    )

    type = models.CharField(
        verbose_name=_('Type'),
        choices=TypeBourse.choices(),
        max_length=50,
    )

    class Meta:
        verbose_name = pgettext_lazy('admission model', 'Scholarship')

    def __str__(self):
        return self.short_name
