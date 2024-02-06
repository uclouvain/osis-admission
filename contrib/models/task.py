# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.contrib.models.base import BaseAdmissionQuerySet


def admission_export_path(task: 'AdmissionTask', filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/exports/{}'.format(
        task.admission.candidate.uuid,
        task.admission.uuid,
        filename,
    )


class AdmissionTaskQuerySet(BaseAdmissionQuerySet):
    training_field_name = 'admission__doctorate_id'


class AdmissionTaskManager(models.Manager.from_queryset(AdmissionTaskQuerySet)):
    pass


class AdmissionTask(models.Model):
    class TaskType(models.TextChoices):
        ARCHIVE = 'ARCHIVE', _('PDF Export')
        CANVAS = 'CANVAS', _('Canvas')
        CONFIRMATION_SUCCESS = 'CONFIRMATION_SUCCESS', _('Confirmation success attestation')
        GENERAL_RECAP = 'GENERAL_RECAP', _('PDF recap for a general education admission')
        CONTINUING_RECAP = 'CONTINUING_RECAP', _('PDF recap for a continuing education admission')
        DOCTORATE_RECAP = 'DOCTORATE_RECAP', _('PDF recap for a doctorate education admission')
        GENERAL_MERGE = 'GENERAL_MERGE', _('Merging of each document field of a general proposition into one PDF')
        CONTINUING_MERGE = 'CONTINUING_MERGE', _(
            'Merging of each document field of a continuing proposition into one PDF',
        )
        DOCTORATE_MERGE = 'DOCTORATE_MERGE', _('Merging of each document field of a doctorate proposition into one PDF')
        GENERAL_FOLDER = 'GENERAL_FOLDER', _('Analysis folder for a general education admission')

    task = models.ForeignKey(
        'osis_async.AsyncTask',
        on_delete=models.CASCADE,
    )
    admission = models.ForeignKey(
        'admission.BaseAdmission',
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        choices=TaskType.choices,
        max_length=20,
    )

    objects = AdmissionTaskManager()
