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


class ExternalPerson(models.Model):
    person = models.OneToOneField(
        'base.Person',
        on_delete=models.CASCADE,
    )
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255,
        blank=True,
        default='',
    )
    institute = models.CharField(
        verbose_name=_("Institution"),
        max_length=255,
        blank=True,
        default='',
    )
    city = models.CharField(
        verbose_name=_("City"),
        max_length=255,
        blank=True,
        default='',
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
