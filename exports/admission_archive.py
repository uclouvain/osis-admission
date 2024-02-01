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
import uuid

from django.db import models
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import AdmissionTask, DoctorateAdmission, SupervisionActor
from admission.contrib.models.doctorate import PropositionProxy
from admission.exceptions import MergePDFException
from admission.exports.utils import admission_generate_pdf
from base.models.enums.person_address_type import PersonAddressType
from base.models.person_address import PersonAddress
from base.models.student import Student
from osis_document.api.utils import confirm_remote_upload, launch_post_processing
from osis_document.enums import PostProcessingType, DocumentExpirationPolicy
from osis_profile.models import EducationalExperience
from osis_signature.enums import SignatureState
from osis_signature.models import StateHistory


def admission_pdf_archive(task_uuid, language=None):
    admission_task = AdmissionTask.objects.select_related('task', 'admission__candidate').get(task__uuid=task_uuid)

    admission: DoctorateAdmission = PropositionProxy.objects.annotate(
        student_registration_id=models.Subquery(
            Student.objects.filter(person_id=models.OuterRef('candidate_id')).values('registration_id')[:1],
        ),
    ).get(uuid=admission_task.admission.uuid)
    addresses = {
        address.label: address
        for address in PersonAddress.objects.filter(
            person=admission.candidate,
            label__in=[PersonAddressType.CONTACT.name, PersonAddressType.RESIDENTIAL.name],
        ).select_related('country')
    }
    date_envoi = (
        StateHistory.objects.filter(
            actor__process=admission.supervision_group,
            state=SignatureState.INVITED.name,
        )
        .order_by('created_at')
        .values('created_at')[:1]
    )
    experiences = EducationalExperience.objects.filter(person=admission.candidate).annotate(
        credits=models.Sum('educationalexperienceyear__acquired_credit_number'),
        first_year=models.Min('educationalexperienceyear__academic_year__year'),
        last_year=models.Max('educationalexperienceyear__academic_year__year'),
    )

    with translation.override(language=language or admission.candidate.language):
        token = admission_generate_pdf(
            admission,
            template='admission/exports/pdf_archive.html',
            filename='pdf_archive.pdf',
            context={
                'contact_address': addresses.get(PersonAddressType.CONTACT.name),
                'residential_address': addresses.get(PersonAddressType.RESIDENTIAL.name),
                "noma": admission.student_registration_id,
                "date_envoi_supervision": date_envoi,
                'allocated_time_label': _("Time allocated for thesis (in %)"),
                'actors': SupervisionActor.objects.filter(process=admission.supervision_group).order_by('-type'),
                'experiences': experiences,
            },
        )

    # Merge project and gantt into PDF
    generated_uuid = confirm_remote_upload(
        token,
        document_expiration_policy=DocumentExpirationPolicy.EXPORT_EXPIRATION_POLICY.value
    )
    output = launch_post_processing(
        uuid_list=[
            str(file_uuid) for file_uuid in [generated_uuid] + admission.project_document + admission.gantt_graph
        ],
        post_processing_types=[PostProcessingType.MERGE.name],
        post_process_params={
            PostProcessingType.MERGE.name: {
                'output_filename': f'pdf_archive_{generated_uuid}',
            },
        },
        async_post_processing=False,
    )

    if output.get('error'):
        raise MergePDFException(output['error'])

    admission.archived_record_signatures_sent = [
        uuid.UUID(output[PostProcessingType.MERGE.name]['output']['upload_objects'][0])
    ]
    admission.save(update_fields=['archived_record_signatures_sent'])
