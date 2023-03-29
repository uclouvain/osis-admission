# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils import translation

from admission.exports.utils import admission_generate_pdf
from admission.contrib.models import AdmissionTask, DoctorateAdmission
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import get_by_label


def admission_pdf_archive(task_uuid, language=None):
    admission_task = AdmissionTask.objects.select_related('task', 'admission__candidate').get(task__uuid=task_uuid)

    admission: DoctorateAdmission = admission_task.admission.doctorateadmission
    with translation.override(language=language or admission.candidate.language):
        contact_address = get_by_label(admission.candidate, PersonAddressType.CONTACT.name)
        residential_address = get_by_label(admission.candidate, PersonAddressType.RESIDENTIAL.name)
        token = admission_generate_pdf(
            admission,
            template='admission/exports/pdf_archive.html',
            filename='pdf_archive.pdf',
            context={
                "contact_address": contact_address,
                "residential_address": residential_address,
            },
        )
    admission.archived_record_signatures_sent = [token]
    admission.save(update_fields=['archived_record_signatures_sent'])
