# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import Subquery

from admission.contrib.models import (
    AdmissionTask,
    GeneralEducationAdmission,
    ContinuingEducationAdmission,
    DoctorateAdmission,
)
from admission.exports.admission_recap.admission_recap import admission_pdf_recap


def _base_education_admission_pdf_recap_from_task(task_uuid: str, admission_class):
    """Generates the admission pdf for an admission and save it."""
    admission = admission_class.objects.select_related(
        'training__academic_year',
        'candidate__country_of_citizenship',
        'candidate__belgianhighschooldiploma',
        'candidate__foreignhighschooldiploma__linguistic_regime',
    ).get(
        pk=Subquery(
            AdmissionTask.objects.values('admission_id').filter(task__uuid=task_uuid)[:1],
        )
    )

    token = admission_pdf_recap(admission, admission.candidate.language)
    admission.pdf_recap = [token]
    admission.save(update_fields=['pdf_recap'])


def general_education_admission_pdf_recap_from_task(task_uuid: str):
    """Generates the admission pdf for a general education admission and save it."""
    _base_education_admission_pdf_recap_from_task(task_uuid, GeneralEducationAdmission)


def continuing_education_admission_pdf_recap_from_task(task_uuid: str):
    """Generates the admission pdf for a continuing education admission and save it."""
    _base_education_admission_pdf_recap_from_task(task_uuid, ContinuingEducationAdmission)


def doctorate_education_admission_pdf_recap_from_task(task_uuid: str):
    """Generates the admission pdf for a doctorate education admission and save it."""
    _base_education_admission_pdf_recap_from_task(task_uuid, DoctorateAdmission)
