##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models
from django.utils.translation import gettext_lazy as _


class ContingenteTraining(models.Model):
    training = models.OneToOneField(
        'base.EducationGroupYear',
        verbose_name=_('Training'),
        on_delete=models.CASCADE,
        editable=False,
        unique=True,
    )
    places_number = models.PositiveSmallIntegerField(
        verbose_name=_('Number of places'),
        default=0,
    )
    last_import_at = models.DateTimeField(
        _("Last import at"),
        null=True,
        editable=False,
    )
    last_import_by = models.ForeignKey(
        'base.Person',
        verbose_name=_("Last import by"),
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
    )
    last_bulk_notification_at = models.DateTimeField(
        _("Last bulk notification at"),
        null=True,
        editable=False,
    )
    last_bulk_notification_by = models.ForeignKey(
        'base.Person',
        verbose_name=_("Last bulk notification by"),
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
    )

    def __str__(self):
        return f'Détail contingente pour {self.training}'
